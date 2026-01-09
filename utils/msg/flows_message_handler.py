from account.models import FacebookMetadata
import requests
from myapp.models import Contact
from .chat_history_handler import *
from decouple import config
from myapp.utils import createMetaComponents

base_url = config("BASE_URL")

def send_agent_message(res, user, payload):
    try:
        if res.get('contacts'):
            recipient_id = res.get('contacts')[0].get('wa_id')
            message_id = res.get('messages')[0].get('id')
            handle_agent_messages(user, recipient_id, payload, message_id)
        else:
            pass
    except:
        pass
    
def send_whatsapp_message(to, text, waba_id, user=None):
    facebook_data = FacebookMetadata.objects.filter(whatsapp_business_account_id=waba_id).first()
    url = f"{base_url}/{facebook_data.api_version}/{facebook_data.phone_id}/messages"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {facebook_data.access_token}"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {
            "body": text
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        print('Payload:-----------', payload, '\n')
        print('Error:-------------', response.json())
        
    res = response.json()
    send_agent_message(res, user if user else facebook_data.user, payload)
        
    return response


def send_whatsapp_image(to, image_url, caption, waba_id, user=None):
    facebook_data = FacebookMetadata.objects.filter(whatsapp_business_account_id=waba_id).first()
    url = f"{base_url}/{facebook_data.api_version}/{facebook_data.phone_id}/messages"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {facebook_data.access_token}"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "image",
        "image": {
            "link": image_url,
            "caption": caption
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        print('Payload:-----------', payload, '\n')
        print('Error:-------------', response.json())
        
    res = response.json()
    send_agent_message(res, user if user else facebook_data.user, payload)
                
    return response


def send_whatsapp_video(to, video_url, caption, waba_id, user=None):
    facebook_data = FacebookMetadata.objects.filter(whatsapp_business_account_id=waba_id).first()
    url = f"{base_url}/{facebook_data.api_version}/{facebook_data.phone_id}/messages"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {facebook_data.access_token}"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "video",
        "video": {
            "link": video_url,
            "caption": caption
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        print('Payload:-----------', payload, '\n')
        print('Error:-------------', response.json())

    res = response.json()
    send_agent_message(res, user if user else facebook_data.user, payload)
        
    return response


def send_whatsapp_document(to, file_url, caption, filename, waba_id, user=None):
    facebook_data = FacebookMetadata.objects.filter(whatsapp_business_account_id=waba_id).first()
    url = f"{base_url}/{facebook_data.api_version}/{facebook_data.phone_id}/messages"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {facebook_data.access_token}"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "DOCUMENT",
        "document": {
            "link": file_url,
            "caption": caption,
            "filename": filename
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        print('Payload:-----------', payload, '\n')
        print('Error:-------------', response.json())

    res = response.json()
    send_agent_message(res, user if user else facebook_data.user, payload)
        
    return response
            

def send_interactive_message(to, item, waba_id, user=None):
    facebook_data = FacebookMetadata.objects.filter(whatsapp_business_account_id=waba_id).first()
    url = f"{base_url}/{facebook_data.api_version}/{facebook_data.phone_id}/messages"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {facebook_data.access_token}"
    }
    if item['interactive']['action'].get('sections'):
        for section in item['interactive']['action']['sections']:
            if section.get('rows'):
                section.pop('id', None)
                section['rows'] = [
                    {
                        'id': row['id'],  # This is allowed inside 'rows'
                        'title': row['title'],
                        'description': row.get('description', '')
                    }
                    for row in section['rows']
                ]
            if section.get('product_items'):
                catalog_id = ''
                for product_item in section.get('product_items'):
                    product_item.pop('name', None)
                    product_item.pop('price', None)
                    product_item.pop('product_catalog', None)
                    catalog_id = product_item.pop('catalog_id', None)
                    
                    product_item.pop('catalog_id', None)
                                                        
                if catalog_id:
                    item['interactive']['action']['catalog_id'] = catalog_id
                
    
    if item['interactive']['action'].get('buttons'):
        for button in item['interactive']['action'].get('buttons'):
            button.pop('triggerMessageId', None)
    
    if item['interactive'].get('type') == "address_message":
        item['interactive']['action']['parameters']['saved_addresses'] = []
        
        contact = Contact.objects.filter(user=FacebookMetadata.objects.filter(whatsapp_business_account_id=waba_id).first().user, full_contact=to).first()
        contact_addresses = contact.addresses.all()
        
        for address in contact_addresses:
            item['interactive']['action']['parameters']['saved_addresses'].append({"id": address.id, "value": address.address})
        
        item['interactive']['action']['parameters']["values"] = {
            "name": contact.name,
            "phone_number": '+' + to,
        }

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": item['interactive']
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        print('Payload:-----------', payload, '\n')
        print('Error:-------------', response.json())

    res = response.json()
    send_agent_message(res, user if user else facebook_data.user, payload)
        
    return response


def send_catalog_message(to, waba_id, order_reference='', user=None):
    facebook_data = FacebookMetadata.objects.filter(whatsapp_business_account_id=waba_id).first()
    url = f"{base_url}/{facebook_data.api_version}/{facebook_data.phone_id}/messages"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {facebook_data.access_token}"
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "catalog_message",
            "body": {
                "text": f"Your order {order_reference} has been placed successfully. You will receive a confirmation soon."
            },
            "footer": {
                "text": "Thank you for shopping with us!"
            },
            "action": {
                "name": "catalog_message",
                # "parameters": {
                #     "product_retailer_id": "102"
                # }
            }
        }
    }
    

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        print('Payload:-----------', payload, '\n')
        print('Error:-------------', response.json())

    res = response.json()
    send_agent_message(res, user if user else facebook_data.user, payload)
        
    return response


def send_template_message(to, template_details, waba_id, user=None):
    facebook_data = FacebookMetadata.objects.filter(whatsapp_business_account_id=waba_id).first()
    url = f"{base_url}/{facebook_data.api_version}/{facebook_data.phone_id}/messages"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {facebook_data.access_token}"
    }
    
    components_without_footer = list(filter(lambda x: x.get('type').lower() not in ['footer'], template_details.get('components')))
    sending_components = list(map(createMetaComponents, components_without_footer))
    
    flat_components = []
    for comp in sending_components:
        if isinstance(comp, list):
            flat_components.extend(comp)
        else:
            flat_components.append(comp)
                    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type" : "individual",
        "to": to,
        "type": "template",
        "template": {
            "name": template_details.get('name'),
            "language": {
                "code": template_details.get('language')
            },
            "components": flat_components
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        print('Payload:-----------', payload, '\n')
        print('Error:-------------', response.json())

    res = response.json()
    send_agent_message(res, user if user else facebook_data.user, template_details)
        
    return response


def fill_product_details(user, product):
    try:
        # Fetch user metadata
        metadata = FacebookMetadata.objects.get(user=user)
        version = metadata.api_version
        access_token = metadata.catalog_access_token or metadata.access_token

        catalog_id = product.order.catalog_id
        if not catalog_id:
            return
        
        url = f"{base_url}/{version}/{catalog_id}/products"
        params = {
            'fields': 'id,description,image_url,name,url,retailer_id',
            'access_token': access_token,
            'limit': 2000000,
        }
        response = requests.get(url, params=params)
        if response.status_code != 200:
            return

        data = response.json().get('data', [])
        for item in data:
            if item.get('retailer_id') == product.product_retailer_id:
                product.product_name = item.get('name', '')
                product.product_description = item.get('description', '')
                product.product_image_url = item.get('image_url', '')
                product.product_url = item.get('url', '')
                product.save()
                break
    
    except FacebookMetadata.DoesNotExist:
        return
    except Exception as e:
        return
