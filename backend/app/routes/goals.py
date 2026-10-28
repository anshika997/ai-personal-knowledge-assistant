from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.goal import Goal, Task
from app.schemas.goal import (
    GoalCreate, GoalOut, GoalUpdate, TaskCreate, TaskOut, TaskUpdate,
)

router = APIRouter(tags=["Goals and Tasks"])


# ---------------- Goals ----------------
@router.post("/goals", response_model=GoalOut, status_code=201)
def create_goal(data: GoalCreate, db: Session = Depends(get_db)):
    goal = Goal(
        title=data.title.strip(),
        description=data.description.strip(),
        target_date=data.target_date,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


@router.get("/goals", response_model=list[GoalOut])
def list_goals(db: Session = Depends(get_db)):
    return db.execute(select(Goal).order_by(Goal.created_at.desc())).scalars().all()


@router.put("/goals/{goal_id}", response_model=GoalOut)
def update_goal(goal_id: int, data: GoalUpdate, db: Session = Depends(get_db)):
    goal = db.get(Goal, goal_id)
    if goal is None:
        raise HTTPException(status_code=404, detail="Goal not found.")

    for field, value in data.model_dump(exclude_unset=True).items():
        # None is allowed only for target_date (to clear the date)
        if value is None and field != "target_date":
            continue
        setattr(goal, field, value.strip() if isinstance(value, str) else value)

    db.commit()
    db.refresh(goal)
    return goal


@router.delete("/goals/{goal_id}", status_code=204)
def delete_goal(goal_id: int, db: Session = Depends(get_db)):
    goal = db.get(Goal, goal_id)
    if goal is None:
        raise HTTPException(status_code=404, detail="Goal not found.")
    db.delete(goal)   # its tasks are deleted too
    db.commit()


# ---------------- Tasks ----------------
@router.post("/goals/{goal_id}/tasks", response_model=TaskOut, status_code=201)
def add_task(goal_id: int, data: TaskCreate, db: Session = Depends(get_db)):
    if db.get(Goal, goal_id) is None:
        raise HTTPException(status_code=404, detail="Goal not found.")
    task = Task(goal_id=goal_id, title=data.title.strip())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.put("/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, data: TaskUpdate, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found.")

    if data.title is not None:
        task.title = data.title.strip()
    if data.is_completed is not None:
        task.is_completed = data.is_completed
        # Remember when it was finished (or clear it if re-opened)
        task.completed_at = datetime.now(timezone.utc) if data.is_completed else None

    db.commit()
    db.refresh(task)
    return task


@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found.")
    db.delete(task)
    db.commit()