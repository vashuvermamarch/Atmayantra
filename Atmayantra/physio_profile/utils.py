import base64

def file_to_b64(file_obj):
    if not file_obj:
        return None
    file_bytes = file_obj.read()
    b64_encoded = base64.b64encode(file_bytes).decode('utf-8')
    return {
        "filename": file_obj.name,
        "content_type": file_obj.content_type,
        "data": b64_encoded
    }

def b64_to_file(b64_dict):
    if not b64_dict:
        return None
    from django.core.files.base import ContentFile
    file_bytes = base64.b64decode(b64_dict["data"])
    return ContentFile(file_bytes, name=b64_dict["filename"])
