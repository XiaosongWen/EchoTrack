from collections import defaultdict
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.commitment import Commitment
from models.commitment_link import CommitmentLink
from models.record import Record
from schemas.commitment import ProgressMetrics


def _compute_streak(dates: list[date], today: date | None = None) -> int:
    """Compute current streak of consecutive dates ending today or yesterday."""
    if not dates:
        return 0
    today = today or date.today()

    runs: list[list[date]] = []
    current_run = [dates[0]]
    for d in dates[1:]:
        gap = (d - current_run[-1]).days
        if gap == 1:
            current_run.append(d)
        elif gap > 1:  # avoid duplicates counting as breaks
            runs.append(current_run)
            current_run = [d]
    runs.append(current_run)

    for run in reversed(runs):
        last = run[-1]
        if last >= today - timedelta(days=1):
            return len(run)
    return 0


class ProgressService:
    @staticmethod
    async def compute_progress(db: AsyncSession, commitment: Commitment) -> ProgressMetrics:
        if commitment.type == 'habit':
            return await ProgressService._compute_habit_progress(db, commitment)
        elif commitment.type == 'goal':
            progress_type = commitment.config.get('progress_type', 'records') if commitment.config else 'records'
            if progress_type == 'checklist':
                return await ProgressService._compute_checklist_progress(db, commitment)
            elif progress_type == 'percentage':
                return await ProgressService._compute_percentage_progress(db, commitment)
            elif progress_type == 'auto_sub':
                return await ProgressService._compute_auto_sub_progress(db, commitment)

        elif commitment.type == 'task':
            return await ProgressService._compute_task_checklist_progress(db, commitment)

        # Default fallback
        return ProgressMetrics(method='records', done=0, total=0, percent=0)

    # ── Batch progress computation ──────────────────────────────────────────

    @staticmethod
    async def compute_progress_batch(
        db: AsyncSession, commitments: list[Commitment],
    ) -> dict[UUID, ProgressMetrics]:
        """Compute progress for multiple commitments with batch queries.

        Returns ``{commitment_id: ProgressMetrics}`` in the same order as
        the input so callers can iterate with ``zip()`` or look up by id.
        """
        if not commitments:
            return {}

        results: dict[UUID, ProgressMetrics] = {}

        # Batch: habit streaks
        habits = [c for c in commitments if c.type == 'habit']
        if habits:
            results.update(await ProgressService._batch_streak_progress(db, habits))

        # Batch: percentage goals
        percentage_goals = [
            c for c in commitments
            if c.type == 'goal' and c.config and c.config.get('progress_type') == 'percentage'
        ]
        if percentage_goals:
            results.update(await ProgressService._batch_percentage_progress(db, percentage_goals))

        # Batch: task checklist items
        tasks = [c for c in commitments if c.type == 'task']
        if tasks:
            results.update(await ProgressService._batch_task_checklist_progress(db, tasks))

        # Fallback for the rest (checklist, auto_sub, unknown types)
        remaining = [c for c in commitments if c.id not in results]
        for c in remaining:
            results[c.id] = await ProgressService.compute_progress(db, c)

        return results

    @staticmethod
    async def _batch_streak_progress(
        db: AsyncSession, habits: list[Commitment], today: date | None = None,
    ) -> dict[UUID, ProgressMetrics]:
        """Single-query streak computation for all habits."""
        ids = [h.id for h in habits]
        rows = (await db.execute(
            select(Record.commitment_id, Record.date)
            .where(Record.commitment_id.in_(ids), Record.status == 'done')
            .order_by(Record.date.asc())
        )).all()

        dates_by_id: dict[UUID, set[date]] = defaultdict(set)
        for row in rows:
            dates_by_id[row.commitment_id].add(row.date)

        today_val = today or date.today()
        return {
            h.id: ProgressMetrics(
                method='streak',
                done=(s := _compute_streak(sorted(list(dates_by_id.get(h.id, set()))), today_val)),
                total=0,
                percent=0,
                streak=s,
            )
            for h in habits
        }

    @staticmethod
    async def _batch_percentage_progress(
        db: AsyncSession, goals: list[Commitment],
    ) -> dict[UUID, ProgressMetrics]:
        """Single-query percentage computation for all goals."""
        ids = [g.id for g in goals]
        rows = (await db.execute(
            select(Record.commitment_id, func.sum(Record.value))
            .where(Record.commitment_id.in_(ids), Record.status == 'done')
            .group_by(Record.commitment_id)
        )).all()

        sums_by_id = dict(rows)

        return {
            g.id: ProgressMetrics(
                method='percentage',
                done=(done := float(sums_by_id.get(g.id, 0) or 0)),
                total=(target := float(g.config.get('target_value', 100))),
                percent=min(100.0, (done / target * 100)) if target > 0 else 0,
            )
            for g in goals
        }

    # ── Single-commitment progress (kept for individual lookups) ────────────

    @staticmethod
    async def _compute_habit_progress(db: AsyncSession, habit: Commitment) -> ProgressMetrics:
        result = await db.execute(
            select(Record.date)
            .where(Record.commitment_id == habit.id, Record.status == 'done')
            .order_by(Record.date.asc())
        )
        dates = list(result.scalars().all())
        streak = _compute_streak(dates)
        return ProgressMetrics(method='streak', done=streak, total=0, percent=0, streak=streak)

    @staticmethod
    async def _compute_checklist_progress(db: AsyncSession, goal: Commitment) -> ProgressMetrics:
        subquery = select(CommitmentLink.child_id).where(CommitmentLink.parent_id == goal.id)
        children = (await db.execute(select(Commitment).where(Commitment.id.in_(subquery)))).scalars().all()

        total = len(children)
        if total == 0:
            return ProgressMetrics(method='checklist', done=0, total=0, percent=0)

        done = sum(1 for c in children if c.status == 'completed')
        percent = (done / total) * 100
        return ProgressMetrics(method='checklist', done=done, total=total, percent=percent)

    @staticmethod
    async def _compute_percentage_progress(db: AsyncSession, goal: Commitment) -> ProgressMetrics:
        target = float(goal.config.get('target_value', 100)) if goal.config else 100
        result = await db.execute(
            select(func.sum(Record.value)).where(Record.commitment_id == goal.id, Record.status == 'done')
        )
        done = float(result.scalar() or 0)
        percent = (done / target * 100) if target > 0 else 0
        percent = min(100.0, percent)
        return ProgressMetrics(method='percentage', done=done, total=target, percent=percent)

    @staticmethod
    async def _compute_auto_sub_progress(db: AsyncSession, goal: Commitment) -> ProgressMetrics:
        # Simplistic approach: average percent of children
        subquery = select(CommitmentLink.child_id).where(CommitmentLink.parent_id == goal.id)
        children = (await db.execute(select(Commitment).where(Commitment.id.in_(subquery)))).scalars().all()

        if not children:
            return ProgressMetrics(method='auto_sub', done=0, total=0, percent=0)

        total_percent = 0
        for child in children:
            child_prog = await ProgressService.compute_progress(db, child)
            total_percent += child_prog.percent

        avg_percent = total_percent / len(children)
        return ProgressMetrics(method='auto_sub', done=0, total=0, percent=avg_percent)

    @staticmethod
    async def _batch_task_checklist_progress(
        db: AsyncSession, tasks: list[Commitment],
    ) -> dict[UUID, ProgressMetrics]:
        """Batch checklist_items progress for all tasks.

        A task is in checklist mode when it has records with sort_order set.
        Progress = done records / total ordered records.
        Tasks with no ordered records get method='records' with zero progress.
        """
        ids = [t.id for t in tasks]
        rows = (await db.execute(
            select(Record.commitment_id, Record.status)
            .where(
                Record.commitment_id.in_(ids),
                Record.sort_order.is_not(None),
            )
        )).all()

        # Group by task
        counts: dict[UUID, dict] = {}
        for row in rows:
            entry = counts.setdefault(row.commitment_id, {'done': 0, 'total': 0})
            entry['total'] += 1
            if row.status == 'done':
                entry['done'] += 1

        result = {}
        for t in tasks:
            if t.id in counts:
                done = counts[t.id]['done']
                total = counts[t.id]['total']
                percent = (done / total * 100) if total > 0 else 0
                result[t.id] = ProgressMetrics(
                    method='checklist_items', done=done, total=total, percent=percent
                )
            else:
                result[t.id] = ProgressMetrics(method='records', done=0, total=0, percent=0)
        return result

    @staticmethod
    async def _compute_task_checklist_progress(db: AsyncSession, task: Commitment) -> ProgressMetrics:
        """Single-task checklist_items progress (used for individual lookups)."""
        rows = (await db.execute(
            select(Record.status)
            .where(Record.commitment_id == task.id, Record.sort_order.is_not(None))
        )).scalars().all()

        total = len(rows)
        if total == 0:
            return ProgressMetrics(method='records', done=0, total=0, percent=0)

        done = sum(1 for s in rows if s == 'done')
        percent = (done / total) * 100
        return ProgressMetrics(method='checklist_items', done=done, total=total, percent=percent)
