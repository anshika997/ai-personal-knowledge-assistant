# Import all models here so Base.metadata knows every table
from app.models.document import Document, DocumentChunk
from app.models.chat import ChatSession, ChatMessage
from app.models.profile import Profile
from app.models.note import Note
from app.models.goal import Goal, Task
from app.models.quiz import QuizAttempt

__all__ = [
    "Document", "DocumentChunk", "ChatSession", "ChatMessage",
    "Profile", "Note", "Goal", "Task", "QuizAttempt",
]