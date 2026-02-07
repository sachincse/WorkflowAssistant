from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from workflows.onboarding import graph
from langchain_core.messages import HumanMessage
from db.mongo import db_handler
import json

router = APIRouter()

class OnboardingRequest(BaseModel):
    employee_name: str
    role: str
    document_path: str

@router.post("/onboard/")
async def start_onboarding(request: OnboardingRequest):
    """
    Starts the onboarding process for a new employee.
    """
    try:
        initial_message = (
            f"Please onboard {request.employee_name} as a {request.role}. "
            f"The ID document is located at {request.document_path}. "
            "Verify the document, provision IT resources, and then create the HR record."
        )
        
        print(f"DEBUG: Starting onboarding for {request.employee_name}")
        
        # Invoke the graph
        # We use invoke for synchronous execution, allowing the graph to run to completion
        output = graph.invoke({"messages": [HumanMessage(content=initial_message)]})
        
        # Serialize messages for storage
        serialized_messages = []
        if "messages" in output:
            for m in output["messages"]:
                msg_type = m.type if hasattr(m, 'type') else 'unknown'
                content = m.content
                name = m.name if hasattr(m, 'name') else None
                serialized_messages.append({"type": msg_type, "name": name, "content": content})

        # Save to MongoDB
        db_id = db_handler.save_conversation(
            request.employee_name, 
            request.role, 
            serialized_messages,
            status="completed"
        )

        return {
            "status": "completed",
            "db_id": db_id,
            "final_state": serialized_messages
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        # Attempt to save failure record
        try:
            db_handler.save_conversation(
                request.employee_name, 
                request.role, 
                [{"type": "error", "content": str(e)}],
                status="failed"
            )
        except:
            pass
        raise HTTPException(status_code=500, detail=str(e))
