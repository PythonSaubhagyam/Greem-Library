from django.http import HttpResponse
from datetime import datetime
import json
from broadcastapp.models import BroadcastHistory, ChatMessage
from django.utils import timezone
from account.models import FacebookMetadata
from django.db import transaction
from utils.responses import HTTPCODE
from catalogs.models import Order, OrderedProduct, Inquiry
from flows_app.models import Flow, FlowMessage
from .flows_message_handler import *
import re
from myapp.models import Contact, ContactAddress, ContactLocation
from django.utils.timezone import make_aware
from utils.msg.chat_history_handler import handle_user_messages
import time
import difflib

def is_match(user_input, button_title, threshold=0.8):
    exact_matches = {
        "interested": ["interested", "i'm interested", "yes", "please", "agree", "want"],
        "not interested": ["not interested", "no", "not at this moment", "decline", "uninterested"]
    }
    
    for keyword, valid_variations in exact_matches.items():
        if user_input==keyword:
            if any(variation in button_title.lower() for variation in valid_variations):
                return True
            return False
        
    ratio = difflib.SequenceMatcher(None, user_input.lower(), button_title.lower()).ratio()
    return ratio >= threshold


# Create new recored according webhook message status respponse
def update_broadcast_history(msg_id, msg_status, button_payload=None):
    try:
        original_msg = BroadcastHistory.objects.get(status=None, message_id=msg_id)
    except BroadcastHistory.DoesNotExist:
        return None

    shared_fields = {
        'user': original_msg.user,
        'broadcast': original_msg.broadcast,
        'template': original_msg.template,
        'template_body': original_msg.template_body,
        'template_id': original_msg.template_id,
        'recipient': original_msg.recipient,
        'recipient_contact': original_msg.recipient_contact,
        'message_id': msg_id,
    }
    if button_payload:
        shared_fields['button_payload'] = button_payload

    # For statuses that can appear only once, rely on get_or_create
    if msg_status not in ["replied", "inquiry"]:
        with transaction.atomic():
            obj, created = BroadcastHistory.objects.get_or_create(
                **shared_fields,
                status=msg_status,
                defaults={'timestamp': timezone.now()}
            )
            if not created:
                # Already exists, skip
                return None
            return obj

    # For statuses that can appear multiple times (replied, inquiry)
    else:
        with transaction.atomic():
            obj = BroadcastHistory.objects.create(
                **shared_fields,
                status=msg_status,
                timestamp=timezone.now()
            )
        return obj

def check_msg_id_and_status(body):
    try:
        status_obj = (
            body.get("entry", [{}])[0]
            .get("changes", [{}])[0]
            .get("value", {})
            .get("statuses", [{}])[0]
        )
        msg_id = status_obj.get("id")
        msg_status = status_obj.get("status")
        timestamp = status_obj.get("timestamp")
        errors = status_obj.get("errors", [])
        if msg_id and msg_status:
            return msg_id, msg_status, timestamp, errors[0] if errors else {}
    except (IndexError, KeyError, TypeError):
        pass
    return False

# Handle Message of Bussiness phone number which send by Customer
def handle_message(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            print(body)

            # try:
            #     requests.post("https://openav-2u8h.onrender.com/webhook", json=body, timeout=5)
            # except Exception as e:
            #     print(e)
            #     pass

            # Check if messages exist
            message_status = check_msg_id_and_status(body)
            if message_status:
                msg_id, status, timestamp, error_payload = message_status
                update_broadcast_history(msg_id, status)

                chat_message = ChatMessage.objects.filter(wa_id=msg_id).first()
                if chat_message:
                    ts = make_aware(datetime.fromtimestamp(int(timestamp)))

                    if status == 'sent':
                        chat_message.sent_at = ts
                    elif status == 'delivered':
                        chat_message.delivered_at = ts
                    elif status == 'read':
                        chat_message.read_at = ts
                        if not chat_message.delivered_at:
                            chat_message.delivered_at = ts
                    elif status == 'failed':
                        chat_message.failure_payload = error_payload
                    chat_message.status = status
                    chat_message.save()
                
                return HttpResponse({"status": "ok"}, status=HTTPCODE.OK)

            messages_exist = 'messages' in body['entry'][0]['changes'][0]['value']
            if messages_exist:
                whatsapp_business_account_id = body['entry'][0]['id']
                fb_meta = FacebookMetadata.objects.filter(whatsapp_business_account_id=whatsapp_business_account_id).first()

                msg_obj = body['entry'][0]['changes'][0]['value']['messages'][0]
                is_context = msg_obj.get('context')
                is_interactive = msg_obj.get('interactive')
                is_location = msg_obj.get('location')
                # If message is just context (and not a referred product, interactive or location message)
                if is_context and not is_context.get('referred_product') and not is_interactive and not is_location:
                    context_id = is_context.get('id')
                    broad_history = update_broadcast_history(context_id, "replied")
                    user = broad_history.user if broad_history else fb_meta.user
                    handle_user_messages(user, msg_obj, user_name=body['entry'][0]['changes'][0]['value']['contacts'][0]['profile']['name'])

                    active_flows = Flow.objects.filter(
                        status=True,
                        is_deleted=False,
                        created_by=user
                    )
                    for flow in active_flows:
                        for flow_message in flow.flow_messages.values():
                            if flow_message['content'] and flow_message['content'][0].get('type').lower() == 'interactive':
                                interactive = flow_message['content'][0].get('interactive')
                                buttons = interactive.get('action').get('buttons', [])
                                for button in buttons:
                                    button_obj = msg_obj.get('button') or {}
                                    reply_obj = button.get('reply') or {}
                                    if is_match(button_obj.get('text', '').lower(), reply_obj.get('title', '').lower()):
                                        button_trigger_message_id = button.get('triggerMessageId')

                                        # default_meg = FlowMessage.objects.filter(default_trigger_message_id=flow_message['message_id']).first()
                                        # if default_meg:
                                        #     content = default_meg.content
                                        #     handle_content(content, msg_obj['from'], whatsapp_business_account_id)
                                        #     time.sleep(2)

                                        update_broadcast_history(context_id, "inquiry", button_payload=button_obj)
                                        process_flow(flow, button_trigger_message_id, msg_obj['from'], whatsapp_business_account_id, user=user)
                                        break

                else:
                    print('\n', body, '\n')
                    changes = body['entry'][0]['changes'][0]['value']
                    message = changes['messages'][0]
                    message_type = message.get('type')

                    if message_type == 'text':
                        msg_text = message['text']['body'].lower()
                        sender_id = message['from']

                        message_payload = {
                            "type": message_type,
                            "text": message['text']['body']
                        }
                        handle_user_messages(fb_meta.user, msg_obj, message_payload=message_payload, user_name=body['entry'][0]['changes'][0]['value']['contacts'][0]['profile']['name'])

                        # Get active flows created by the business user associated with this WhatsApp account.
                        active_flows = Flow.objects.filter(
                            status=True,
                            is_deleted=False,
                            created_by=fb_meta.user
                        )

                        found_match = False
                        for flow in active_flows:
                            for flow_message in flow.flow_messages.values():
                                if flow_message['message_id'] == "keyword":
                                    regex_case_sensitive = flow_message.get('regex_case_sensitive', False)

                                    if regex_case_sensitive:
                                        content = flow_message.get('content', [])  # JSON stored content
                                        regex_pattern = content[0].get('regex', '') if content else None
                                        if regex_pattern and re.search(regex_pattern, msg_text):
                                            send_whatsapp_message(sender_id, f"Hello *{body['entry'][0]['changes'][0]['value']['contacts'][0]['profile']['name']}*", fb_meta.whatsapp_business_account_id)

                                            process_flow(flow, flow_message['trigger_message_id'], sender_id, whatsapp_business_account_id)
                                            found_match = True

                                            contact = Contact.objects.filter(
                                                user=fb_meta.user,
                                                full_contact=sender_id
                                            ).first()
                                            if contact:
                                                contact.active_flow = flow
                                                contact.save()

                                            continue

                                    keywords = flow_message.get('keywords', [])
                                    if any(keyword.lower().strip() in msg_text for keyword in keywords):

                                        send_whatsapp_message(sender_id, f"Hello *{body['entry'][0]['changes'][0]['value']['contacts'][0]['profile']['name']}*", fb_meta.whatsapp_business_account_id)

                                        process_flow(flow, flow_message['trigger_message_id'], sender_id, whatsapp_business_account_id)
                                        found_match = True

                                        contact = Contact.objects.filter(
                                            user=fb_meta.user,
                                            full_contact=sender_id
                                        ).first()
                                        if contact:
                                            contact.active_flow = flow
                                            contact.save()

                            if found_match:
                                break

                    # Handle interactive messages
                    elif message_type == 'interactive':
                        interactive = message.get('interactive')
                        sender_id = message.get('from')
                        interactive_type = interactive.get('type')

                        message_payload = {
                            "type": message_type,
                            "interactive": interactive
                        }
                        handle_user_messages(fb_meta.user, msg_obj, message_payload=message_payload, user_name=body['entry'][0]['changes'][0]['value']['contacts'][0]['profile']['name'])

                        if interactive_type == 'list_reply':
                            selected_option_id = interactive['list_reply'].get('id')
                            process_interactive_selection(sender_id, selected_option_id, whatsapp_business_account_id)
                        elif interactive_type == 'button_reply':
                            selected_option_id = interactive['button_reply'].get('id')
                            process_interactive_selection(sender_id, selected_option_id, whatsapp_business_account_id)
                        elif interactive_type == 'nfm_reply':
                            contacts = Contact.objects.filter(
                                user=fb_meta.user,
                                full_contact=message.get('from')
                            ).first()

                            # Parse the response JSON from nfm_reply
                            if interactive['nfm_reply'].get('name') == 'address_message':
                                address_json = json.loads(interactive['nfm_reply'].get('response_json', '{}'))

                                if contacts:
                                    if address_json.get('saved_address_id'):
                                        address = ContactAddress.objects.get(id=int(address_json.get('saved_address_id')))
                                    else:
                                        address = ContactAddress.objects.filter(body=interactive['nfm_reply'].get('body')).first()
                                        if not address:
                                            address = ContactAddress.objects.create(
                                                address=address_json.get('values') if address_json.get('values') else address_json,
                                                body=interactive['nfm_reply'].get('body')
                                            )
                                            contacts.addresses.add(address)
                                    contacts.latest_address = address
                                    contacts.save()

                            if interactive['nfm_reply'].get('name') == 'flow':
                                flow_json = json.loads(interactive['nfm_reply'].get('response_json', '{}'))
                                inquiry = Inquiry.objects.create(
                                    flow_response=flow_json,
                                    user=fb_meta.user,
                                    phone_number=sender_id,
                                    full_name=body['entry'][0]['changes'][0]['value']['contacts'][0]['profile']['name'],
                                )

                            active_flow = contacts.active_flow if contacts else None
                            if not active_flow:
                                fallback_text = None
                            else:
                                intents = active_flow.intents

                                default_intent = intents.get("Order", {})

                                if default_intent.get("isEnabled", False):
                                    fallback_text = default_intent.get("message", None)
                                else:
                                    fallback_text = None

                            if fallback_text:
                                if default_intent.get('messageType') == "TEXT":
                                    send_whatsapp_message(sender_id, fallback_text, whatsapp_business_account_id)
                                elif default_intent.get('messageType') == "IMAGE":
                                    send_whatsapp_image(sender_id, default_intent.get('url'), fallback_text, whatsapp_business_account_id)
                                elif default_intent.get('messageType') == "VIDEO":
                                    send_whatsapp_video(sender_id, default_intent.get('url'), fallback_text, whatsapp_business_account_id)


                    # Handle location messages
                    elif message_type == 'location':
                        sender_id = message.get('from')
                        contacts = Contact.objects.filter(
                            user=fb_meta.user,
                            full_contact=sender_id
                        ).first()
                        if contacts:
                            message_loc = message.get('location')
                            location = ContactLocation.objects.create(
                                address=message_loc.get("address"),
                                latitude=message_loc.get("latitude"),
                                longitude=message_loc.get("longitude"),
                                name=message_loc.get("name")
                            )
                            contacts.locations.add(location)
                            contacts.save()

                        message_payload = {
                            "type": message_type,
                            "location": message.get('location')
                        }
                        handle_user_messages(fb_meta.user, msg_obj, message_payload=message_payload, user_name=body['entry'][0]['changes'][0]['value']['contacts'][0]['profile']['name'])


                    # Handle order messages
                    elif message_type == 'order':
                        order_data = message.get('order')
                        order_id = message.get('id')
                        sender_id = message.get('from')
                        catalog_id = order_data.get('catalog_id')
                        customer_name = changes['contacts'][0]['profile'].get('name')
                        customer_phone = changes['contacts'][0].get('wa_id')
                        currency = order_data['product_items'][0].get('currency')
                        # Calculate total amount
                        total_amount = sum(item['item_price'] * item['quantity'] for item in order_data.get('product_items', []))

                        message_payload = {
                            "type": message_type,
                            "order": order_data
                        }
                        handle_user_messages(fb_meta.user, msg_obj, message_payload=message_payload, user_name=body['entry'][0]['changes'][0]['value']['contacts'][0]['profile']['name'])

                        contact = Contact.objects.filter(
                            user=fb_meta.user,
                            full_contact=sender_id
                        ).first()

                        order = Order.objects.create(
                            order_id=order_id,
                            customer=contact,
                            customer_name=customer_name,
                            customer_phone=customer_phone,
                            catalog_id=catalog_id,
                            total_amount=total_amount,
                            currency=currency,
                            user=fb_meta.user,
                        )

                        for item in order_data.get('product_items', []):
                            OrderedProduct.objects.create(
                                order=order,
                                product_retailer_id=item.get('product_retailer_id'),
                                quantity=item.get('quantity'),
                                item_price=item.get('item_price'),
                                total_price=item.get('item_price') * item.get('quantity')
                            )

                        ordered_products = order.products.all()
                        for product in ordered_products:
                            if (
                                not product.product_name and
                                not product.product_description and
                                not product.product_image_url and
                                not product.product_url
                            ):
                                fill_product_details(fb_meta.user, product)

                        payload = {
                            "type": "interactive",
                            "interactive": {
                                "type": "address_message",
                                "body": {
                                    "text": "Please Provide the Address"
                                },
                                "action": {
                                    "name": "address_message",
                                    "parameters": {
                                        "country": "IN"
                                    }
                                }
                            }
                        }
                        send_interactive_message(sender_id, payload, fb_meta.whatsapp_business_account_id)

                    else:
                        handle_user_messages(fb_meta.user, msg_obj, user_name=body['entry'][0]['changes'][0]['value']['contacts'][0]['profile']['name'])
                        
            return HttpResponse({"status": "ok"}, status=HTTPCODE.OK)

        except Exception as e:
            print(f"unknown error: {e}")
            return HttpResponse({"status": "error", "message": str(e)}, status=HTTPCODE.SERVER_ERROR)

    return HttpResponse({"status": "error", "message": "Method not allowed"}, status=HTTPCODE.METHOD_NOT_ALLOWED)


def handle_content(content, to, waba_id, user=None):
    for item in content:
        if item['type'].lower() == 'text':
            send_whatsapp_message(to, item['text'], waba_id, user=user)
        elif item['type'].lower() == 'image':
            send_whatsapp_image(to, item['url'], item['caption'], waba_id, user=user)
        elif item['type'].lower() == 'interactive':
            send_interactive_message(to, item, waba_id, user=user)
        elif item['type'].lower() == 'video':
            send_whatsapp_video(to, item['url'], item['caption'], waba_id, user=user)
        elif item['type'].lower() == 'file':
            send_whatsapp_document(to, item['url'], item['caption'], item['filename'], waba_id, user=user)
        elif item['type'].lower() == 'template':
            send_template_message(to, item['template'], waba_id, user=user)
        else:
            print(f"Unsupported content type: {item['type']}")


def process_flow(flow, trigger_message_id, to, waba_id, user=None):
    for flow_message in flow.flow_messages.values():
        if flow_message['message_id'] == trigger_message_id:
            content = flow_message.get('content', [])
            handle_content(content, to, waba_id, user=user)

            # Check for next trigger in flow nodes
            next_trigger_id = flow_message.get('default_trigger_message_id')
            if next_trigger_id:
                time.sleep(1)
                return process_flow(flow, next_trigger_id, to, waba_id, user=user)
    return True


def process_interactive_selection(to, option_id, wa_id):
    """
    Processes the interactive selection by:
    1. Extracting the node id from the option_id.
    2. Finding the FlowMessage record with that node id.
    3. Searching its content for a row with a matching option_id.
    4. Extracting the triggerMessageId and sending the next message.
    """
    # Step 1: Extract the node id from the option_id.
    prefix = ("list_message-right-", "message_with_button-")  # Convert list to tuple
    matching_prefix = next((p for p in prefix if option_id.startswith(p)), None)

    if not matching_prefix:
        send_default_message(to, wa_id)
        return

    # Remove prefix and split the remaining string by '-'
    remaining = option_id[len(matching_prefix):]  # e.g. "1739882973608-0-1739883218393-|67b2d56990f9c40849277316-|67b2d56990f9c40849277316"
    parts = remaining.split('+')
    if len(parts) < 1:
        send_default_message(to, wa_id)
        return

    node_id_extracted = parts[1]  # "1739882973608"

    # Step 2: Find the FlowMessage record with this node id.
    parent_message = FlowMessage.objects.filter(message_id=node_id_extracted).first()
    if not parent_message:
        send_default_message(to, wa_id)
        return

    # Step 3: In the parent's content JSON, find the row that matches our full option_id.
    interactive_content = parent_message.content or {}
    sections = interactive_content[0].get('interactive', {}).get("action", {}).get("sections", [])
    trigger_message_id = None

    if sections:
        for section in sections:
            rows = section.get("rows", [])
            for row in rows:
                if row.get("id") == option_id:
                    trigger_message_id = row.get("triggerMessageId")
                    break
            if trigger_message_id:
                break
    else:
        buttons = interactive_content[0].get('interactive', {}).get("action", {}).get("buttons", [])
        for button in buttons:
            if button.get('reply').get('id') == option_id:
                trigger_message_id = button.get("triggerMessageId")
                break

    if not trigger_message_id:
        send_default_message(to, wa_id)
        return

    # Step 4: Use the triggerMessageId to find the next message.
    next_message = FlowMessage.objects.filter(message_id=trigger_message_id).first()
    if next_message:
        send_flow_message(to, next_message, wa_id)
    else:
        send_default_message(to, wa_id)


def send_flow_message(to, message, waba_id):
    content = message.content
    handle_content(content, to, waba_id)

    next_trigger_id = message.default_trigger_message_id
    if next_trigger_id:
        time.sleep(1)
        return process_flow(message.flow, next_trigger_id, to, waba_id)


def send_default_message(to, wa_id):
    fb_meta = FacebookMetadata.objects.filter(whatsapp_business_account_id=wa_id).first()

    contact = None
    if fb_meta and fb_meta.user:
        contact = Contact.objects.filter(
            user=fb_meta.user,
            full_contact=to
        ).first()
        
    active_flow = contact.active_flow if contact else None

    if not active_flow:
        fallback_text = None
    else:
        intents = active_flow.intents

        default_intent = intents.get("Default", {})

        if default_intent and default_intent.get("isEnabled", False):
            fallback_text = default_intent.get("message", None)
        else:
            fallback_text = None

    if fallback_text:
        if default_intent.get('messageType') == "TEXT":
            send_whatsapp_message(to, fallback_text, wa_id)
        elif default_intent.get('messageType') == "IMAGE":
            send_whatsapp_image(to, default_intent.get('url'), fallback_text, wa_id)
        elif default_intent.get('messageType') == "VIDEO":
            send_whatsapp_video(to, default_intent.get('url'), fallback_text, wa_id)


