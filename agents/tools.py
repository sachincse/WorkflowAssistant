from langchain_core.tools import tool

@tool
def verify_document(document_path: str):
    """
    Verifies the uploaded document for authenticity and validity.
    
    Args:
        document_path: The file path of the document to verify.
    """
    # In a real app, this would use OCR or an external API
    print(f"DEBUG: Verifying document at {document_path}")
    return {"status": "valid", "type": "ID", "details": "Government issued ID verified."}

@tool
def provision_it_resources(employee_name: str, role: str):
    """
    Provisions It resources (email, accounts) for a new employee.
    
    Args:
        employee_name: Name of the employee.
        role: Job role of the employee to determine access levels.
    """
    print(f"DEBUG: Provisioning IT resources for {employee_name} ({role})")
    email = f"{employee_name.lower().replace(' ', '.')}@company.com"
    return {
        "email": email,
        "slack_channel": "#general",
        "software": ["Office365", "Jira"] if "dev" not in role.lower() else ["Office365", "Jira", "GitHub"]
    }

@tool
def create_hr_record(employee_name: str, email: str, documents_verified: bool):
    """
    Creates an HR record and sends a welcome packet.
    
    Args:
        employee_name: Name of the employee.
        email: Provisioned email address.
        documents_verified: Boolean indicating if documents were verified.
    """
    if not documents_verified:
        return {"error": "Cannot create HR record. Documents not verified."}
    
    print(f"DEBUG: Creating HR record for {employee_name}")
    return {"status": "onboarded", "employee_id": "EMP-9999", "message": "Welcome email sent."}
