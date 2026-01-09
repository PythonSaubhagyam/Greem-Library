from myapp.models import Contact
from broadcastapp.models import Conversation, ChatMessage
from datetime import datetime
from django.utils.timezone import make_aware
import phonenumbers

def extract_cc_and_number(full_contact):
    """
    Extracts country code and mobile number from a full contact string using phonenumbers.
    """
    try:
        parsed_number = phonenumbers.parse(f"+{full_contact}" if not full_contact.startswith("+") else full_contact)
        cc = str(parsed_number.country_code)
        contact = full_contact[len(cc):]  # Remove country code from original number
        return cc, contact
    except phonenumbers.phonenumberutil.NumberParseException:
        return "", full_contact  # If parsing fails, return full number as contact

def handle_agent_messages(user, recipient_id, template_details, message_id):
    try:
        # track which number matched
        matched_number = None

        contact = Contact.objects.filter(user=user, full_contact=recipient_id).first()
        if contact:
            matched_number = contact.full_contact
        else:
            contact = Contact.objects.filter(user=user, contact=recipient_id).first()
            if contact:
                matched_number = contact.contact
            else:
                contact = Contact.objects.filter(user=user, whatsapp_given_number=recipient_id).first()
                if contact:
                    matched_number = contact.whatsapp_given_number

        if not contact:
            # no contact at all
            matched_number = recipient_id

        # now use matched_number (fallback to recipient_id)
        matched_number = matched_number or recipient_id

        # look for existing conversation with this matched number
        contact_conversation = Conversation.objects.filter(
            user=user,
            user_number=matched_number
        ).first()

        if not contact_conversation:
            contact_conversation = Conversation.objects.create(
                user=user,
                user_number=matched_number,
                user_name=contact.name if contact else "",
                contact=contact
            )

        # attach contact if it was missing
        if contact_conversation and contact and not contact_conversation.contact:
            contact_conversation.contact = contact
            contact_conversation.save()

        # create chat message
        ChatMessage.objects.create(
            conversation=contact_conversation,
            contact=contact,
            user_number=recipient_id,  # WhatsApp’s actual number for this message
            user_name=contact.name if contact else "",
            sender="Agent",
            payload=template_details,
            wa_id=message_id,
        )

    except Exception as e:
        print(f'Error Handling Agent Messages: {e}')
        pass
                    

def handle_user_messages(user, msg_obj, message_payload=None, user_name=None):
    try:
        recipient_id = msg_obj.get('from')  # WhatsApp's sender ID

        # Extract cc and contact from full number
        cc, contact_number = extract_cc_and_number(recipient_id)

        # 1️⃣ Try to find existing contact by any of the three fields
        contact = Contact.objects.filter(user=user, full_contact=recipient_id).first()
        matched_number = None

        if contact:
            matched_number = contact.full_contact
        else:
            contact = Contact.objects.filter(user=user, contact=contact_number).first()
            if contact:
                matched_number = contact.contact
            else:
                contact = Contact.objects.filter(user=user, whatsapp_given_number=recipient_id).first()
                if contact:
                    matched_number = contact.whatsapp_given_number

        # 2️⃣ If no contact at all, create a brand-new one using WhatsApp number
        if not contact:
            contact = Contact.objects.create(
                user=user,
                full_contact=recipient_id,
                name=recipient_id if not user_name else user_name,
                cc=cc,
                contact=contact_number,
                whatsapp_given_number=recipient_id
            )
            matched_number = recipient_id

        matched_number = matched_number or recipient_id

        # 3️⃣ Find existing conversation by matched number
        contact_conversation = Conversation.objects.filter(
            user=user,
            user_number=matched_number
        ).first()

        if not contact_conversation:
            contact_conversation = Conversation.objects.create(
                user=user,
                user_number=matched_number,
                user_name=contact.name,
                contact=contact,
            )

        if contact_conversation and not contact_conversation.contact:
            contact_conversation.contact = contact
            contact_conversation.save()

        # 4️⃣ Create chat message
        time_stamp = int(msg_obj.get('timestamp'))
        timestamp_dt = make_aware(datetime.fromtimestamp(time_stamp))

        payload = message_payload or msg_obj.get(msg_obj.get('type'))

        ChatMessage.objects.create(
            conversation=contact_conversation,
            contact=contact,
            user_number=recipient_id,  # actual WA number from this message
            user_name=contact.name,
            sender="User",
            message_type=msg_obj.get('type'),
            payload=payload,
            sent_at=timestamp_dt,
            delivered_at=make_aware(datetime.now()),
            status='delivered',
            wa_id=msg_obj.get('id'),
            context=msg_obj.get('context') or {},
        )

        # update conversation last active
        contact_conversation.last_active = timestamp_dt
        contact_conversation.save()

    except Exception as e:
        print(f'Error Handling User Messages: {e}')
        pass
