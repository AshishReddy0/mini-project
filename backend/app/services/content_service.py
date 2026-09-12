# Generated content service — revision, exam, and quiz records.
# Phase 2 stores placeholder content; Phase 3 connects Gemini API.

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.generated_content import ContentType, GeneratedContent
from app.models.workspace import Workspace
from app.schemas.content import ContentGenerateRequest
from app.services.gemini_service import generate_content
from app.models.document import Document


def build_workspace_text(workspace: Workspace) -> str:
    text = ""

    for document in workspace.documents:
        if document.extracted_text:
            text += document.extracted_text.content + "\n"

    return text

# Shown until Phase 3 AI generation is implemented



def list_content(db: Session, workspace: Workspace) -> list[GeneratedContent]:
    """Return all generated content for a workspace."""
    return (
        db.query(GeneratedContent)
        .filter(GeneratedContent.workspace_id == workspace.id)
        .order_by(GeneratedContent.created_at.desc())
        .all()
    )


def get_content(
    db: Session, workspace: Workspace, content_id: UUID
) -> GeneratedContent:
    """Fetch a single generated content item."""
    item = (
        db.query(GeneratedContent)
        .filter(
            GeneratedContent.id == content_id,
            GeneratedContent.workspace_id == workspace.id,
        )
        .first()
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generated content not found",
        )
    return item


def create_content(
    db: Session,
    workspace: Workspace,
    content_type: ContentType,
    data: ContentGenerateRequest,
) -> GeneratedContent:

    document_text = ""

    if data.document_id:
        selected_document = None

        for document in workspace.documents:
            if str(document.id) == str(data.document_id):
                selected_document = document
                break

        if not selected_document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Selected document not found",
        )

        if selected_document.extracted_text:
           document_text = selected_document.extracted_text.content

    else:
       document_text = build_workspace_text(workspace)

    if not document_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No extracted study material found in workspace",
        )

    if content_type == ContentType.REVISION:
        prompt = f"""
        You are an expert academic tutor. Generate a highly structured, comprehensive Revision Guide on the topic "{data.topic}" (or the entire context if no topic is specified) based on this material:

        {document_text}

        Structure the response using clean Markdown with:
        - A clear Title (# heading) and Brief Overview.
        - **Key Concepts & Definitions**: Bold key terms and provide precise, easy-to-understand definitions.
        - **Main Topics**: Break down the topic using subheadings (##, ###) and bullet points.
        - **Comparison Tables**: Use Markdown tables where appropriate to compare different concepts or options.
        - **Takeaways**: A bulleted list of key takeaways at the end.

        Ensure the language is academic yet accessible. Format beautifully and cleanly.
        """

    elif content_type == ContentType.EXAM:
        prompt = f"""
        You are an academic examiner. Generate a structured, solved Exam Preparation Guide on the topic "{data.topic}" (or the entire context if no topic is specified) based on this material:

        {document_text}

        Generate high-quality exam-style questions with detailed, structured answers.
        
        For EVERY 5-mark and 10-mark question, you MUST generate an **Exam Coaching Box** directly below the question (before the model answer).
        The coaching box should contain:
        - **Keywords checklist**: Important technical terms examiners scan for.
        - **Common Pitfalls**: Frequent mistakes where students lose marks on this topic.
        - **Suggested Layout Checklist**: Recommended structural outline (e.g. Intro, flow diagram, equations, components, conclusion).

        Required solved questions:
        1. **2-Mark Questions (Short Answers)**: Precision definitions and single-sentence explanations. (Generate exactly 3 questions with answers)
        2. **5-Mark Questions (Medium Answers)**: Solved explanations with bullet points and clear examples. Include the Exam Coaching Box. (Generate exactly 2 questions with answers)
        3. **10-Mark Questions (Long Answers)**: Solved comprehensive answers structured with Introduction, Detailed Explanation, Working, Pros/Cons, and Conclusion. Include the Exam Coaching Box. (Generate exactly 1 question with answer)

        Format the guide using clean Markdown. Use subheadings (##) for each question category, and bold text for questions. Wrap the Exam Coaching Box inside a markdown blockquote (starting with `> `) to make it visually distinct.
        """

    elif content_type == ContentType.QUIZ:
        question_count = data.question_count or 10
        
        prompt = f"""
        Generate {question_count} MCQs.

        Text:

        {document_text}

        Return ONLY valid JSON.
        Do not add explanation, headings, markdown, or extra text.
        Format:
        [
            {{
                "question": "...",
                "options": {{
                  "A": "...",
                  "B": "...",
                  "C": "...",
                  "D": "..."
                }},
                "answer": "A"
            }}
        ]
        """

    elif content_type == ContentType.LOGIC_FLOW:
        prompt = f"""
        Analyze the following academic document context:

        {document_text}

        Generate a detailed, step-by-step logic flow or process flow diagram/sequence for the topic: "{data.topic or 'the main process/algorithm described in the text'}".

        Provide a logical sequence of 4 to 10 steps representing the flow of operations, decision points, state transitions, or loops.
        Define clear step titles, descriptions, types, and branching logic.

        Return ONLY a valid JSON object.
        Do not add explanation outside the JSON. Do not wrap the JSON in markdown code blocks.

        Format:
        {{
          "title": "Overall Logic Flow Title",
          "description": "Short explanation of the flow and its purpose",
          "steps": [
            {{
              "id": 1,
              "title": "Step Title",
              "description": "Clear explanation of what happens in this step, referencing key concepts from the context.",
              "type": "action",
              "next_step_id": 2
            }},
            {{
              "id": 2,
              "title": "Decision Check",
              "description": "Explain the check or branch condition here.",
              "type": "condition",
              "yes_step_id": 3,
              "no_step_id": 4
            }},
            {{
              "id": 3,
              "title": "Yes Branch Action",
              "description": "Explanation of the path taken when condition is met.",
              "type": "action",
              "next_step_id": 5
            }},
            {{
              "id": 4,
              "title": "No Branch Action",
              "description": "Explanation of the path taken when condition is not met.",
              "type": "action",
              "next_step_id": 5
            }},
            {{
              "id": 5,
              "title": "Ending Step",
              "description": "Final step or conclusion of the process.",
              "type": "end"
            }}
          ]
        }}

        Allowed "type" values: "start", "action", "condition", "loop", "end".
        Make sure all referenced step IDs exist.
        """

    needs_json = content_type in (ContentType.QUIZ, ContentType.LOGIC_FLOW)
    generated_text = generate_content(prompt, expect_json=needs_json)

    default_titles = {
        ContentType.REVISION: "Revision Notes",
        ContentType.EXAM: "Exam Preparation",
        ContentType.QUIZ: "Practice Quiz",
        ContentType.LOGIC_FLOW: "Logic Flow Diagram",
    }

    title = data.title or default_titles[content_type]

    item = GeneratedContent(
        workspace_id=workspace.id,
        content_type=content_type,
        title=title,
        content=generated_text,
        metadata_json={
            "topic": data.topic,
            "phase": 3,
            "generated_by": "gemini"
        },
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return item
def delete_content(db: Session, workspace, content_id):
    content = get_content(db, workspace, content_id)
    db.delete(content)
    db.commit()