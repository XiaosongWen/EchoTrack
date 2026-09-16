import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import usePursuitsStore from "../stores/pursuitsStore";
import LabelPill from "../components/pursuits/LabelPill";
import { formatLocalDateShort } from "../utils/date";
import HabitChecklist from "../components/pursuits/HabitChecklist";
import GoalCard from "../components/pursuits/GoalCard";
import TaskCard from "../components/pursuits/TaskCard";
import CreateCommitmentModal from "../components/pursuits/CreateCommitmentModal";
import InlineCalendar from "../components/pursuits/InlineCalendar";
import CommitmentDetail from "./CommitmentDetail";

const FILTERS = ["all", "habit", "goal", "task"];
const PRIORITY_WEIGHT = { high: 3, medium: 2, med: 2, low: 1, none: 0 };

const TAB_MAP = {
  all: "all",
  habits: "habit",
  habit: "habit",
  goals: "goal",
  goal: "goal",
  tasks: "task",
  task: "task",
};

export default function Commitments() {
  const { tab } = useParams();
  const navigate = useNavigate();
  const { commitments, labels, daily, records, fetchCommitments, fetchLabels, fetchDaily, fetchRecords, uncheckHabit, checkInHabit, updateCommitment, loading, error } = usePursuitsStore();
  
  const filter = TAB_MAP[tab] || "all";

  const handleSetFilter = (newFilter) => {
    const routeMap = {
      all: "/commitments/all",
      habit: "/commitments/habits",
      goal: "/commitments/goals",
      task: "/commitments/tasks",
    };
    navigate(routeMap[newFilter] || "/commitments");
  };
  const [searchQuery, setSearchQuery] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [createType, setCreateType] = useState(null);
  const [editingCommitment, setEditingCommitment] = useState(null);
  const [selectedDetailId, setSelectedDetailId] = useState(null);
  const [rescheduleTaskId, setRescheduleTaskId] = useState(null);
  const [clearParentIdOnReschedule, setClearParentIdOnReschedule] = useState(false);

  const handlePromptReschedule = (taskId, clearParent = false) => {
    setRescheduleTaskId(taskId);
    setClearParentIdOnReschedule(clearParent);
  };

  const now = new Date();
  const todayISO = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;

  useEffect(() => {
    fetchCommitments();
    fetchLabels();
    fetchDaily(todayISO);
    fetchRecords({ status: "done" });
  }, [fetchCommitments, fetchLabels, fetchDaily, fetchRecords, todayISO]);

  const query = searchQuery.trim().toLowerCase();
  const filteredCommitments = commitments.filter((c) => {
    if (!query) return true;
    const matchTitle = c.title?.toLowerCase().includes(query);
    const matchLabels = (c.labels || []).some((lbl) => lbl.name?.toLowerCase().includes(query));
    return matchTitle || matchLabels;
  });

  const habits = filteredCommitments.filter((c) => c.type === "habit" && c.status === "active");
  const goals = filteredCommitments.filter((c) => c.type === "goal" && c.status === "active");
  const tasks = filteredCommitments.filter((c) => c.type === "task");

  const openCreate = (type) => {
    setCreateType(type);
    setEditingCommitment(null);
    setShowCreate(true);
  };

  const handleHabitCheckIn = (habitId, existingRecordId) => {
    if (existingRecordId) {
      uncheckHabit(habitId, existingRecordId);
    } else {
      checkInHabit(habitId);
    }
  };

  return (
    <div className="view active" id="pursuits">
      <header className="page-header">
        <h1>Pursuits</h1>
      </header>

      <div className="toolbar">
        <div className="filters">
          {FILTERS.map((f) => (
            <button
              key={f}
              className={`filter-btn${filter === f ? " active" : ""}`}
              onClick={() => handleSetFilter(f)}
            >
              {f === "all" ? "All" : f.charAt(0).toUpperCase() + f.slice(1) + "s"}
            </button>
          ))}
        </div>
        <div style={{ display: "flex", gap: "12px" }}>
          <div className="input-bar" style={{ background: "var(--bg)" }}>
            <span>🔍</span>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search commitments..."
              style={{ width: 170 }}
            />
          </div>
          <button className="btn-primary" onClick={() => openCreate(filter === "all" ? null : filter)}>
            + New ▾
          </button>
        </div>
      </div>

      {loading && <div className="text-muted text-sm" style={{ marginTop: 16 }}>Loading...</div>}
      {error && <div style={{ color: "var(--danger)", marginTop: 16 }}>{error}</div>}

      <div className="content-container">
        {/* ALL SUMMARY */}
        {filter === "all" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 32 }}>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 24 }}>
              <SummaryCard
                icon="🔄"
                label="Habits"
                count={habits.length}
                items={[...habits]
                  .sort((a, b) => (b.progress?.streak ?? 0) - (a.progress?.streak ?? 0))
                  .slice(0, 5)
                  .map((h) => {
                    const streak = h.progress?.streak ?? 0;
                    const days = streak % 7;
                    const weeks = Math.floor(streak / 7);
                    return {
                      left: h.title,
                      labels: h.labels || [],
                      right: `🔥 ${days}d ${weeks}w`,
                    };
                  })}
                onClick={() => handleSetFilter("habit")}
              />
              <SummaryCard
                icon="🎯"
                label="Goals"
                count={goals.length}
                items={goals.slice(0, 5).map((g) => {
                  const subGoals = commitments.filter((c) => c.parent_id === g.id || (c.type === "sub-goal" && c.parent_id === g.id));
                  let percent = Math.round(g.progress?.percent ?? 0);
                  if (subGoals.length > 0) {
                    const doneCount = subGoals.filter((s) => s.status === "completed").length;
                    percent = Math.round((doneCount / subGoals.length) * 100);
                  }
                  return {
                    left: g.title,
                    labels: g.labels || [],
                    right: `${percent}%`,
                  };
                })}
                onClick={() => handleSetFilter("goal")}
              />
              <SummaryCard
                icon="📋"
                label="Tasks"
                count={tasks.filter((t) => t.status === "active").length}
                items={[...tasks]
                  .sort((a, b) => {
                    const aDone = a.status === "completed";
                    const bDone = b.status === "completed";
                    if (aDone && !bDone) return 1;
                    if (!aDone && bDone) return -1;
                    if (aDone && bDone) {
                      const timeA = new Date(a.updated_at || a.completed_at || 0).getTime();
                      const timeB = new Date(b.updated_at || b.completed_at || 0).getTime();
                      return timeB - timeA;
                    }
                    const getBucket = (t) => {
                      if (t.due_date && t.due_date === todayISO) return 0;
                      if (!t.due_date) return 1;
                      return 2;
                    };
                    const bucketA = getBucket(a);
                    const bucketB = getBucket(b);
                    if (bucketA !== bucketB) return bucketA - bucketB;
                    const weightA = PRIORITY_WEIGHT[a.priority?.toLowerCase()] ?? 0;
                    const weightB = PRIORITY_WEIGHT[b.priority?.toLowerCase()] ?? 0;
                    if (weightB !== weightA) return weightB - weightA;
                    return new Date(a.created_at || 0).getTime() - new Date(b.created_at || 0).getTime();
                  })
                  .slice(0, 5)
                  .map((t) => ({
                    left: t.title,
                    labels: t.labels || [],
                    right: t.status === "completed" ? "Done" : (t.due_date ? formatLocalDateShort(t.due_date) : (t.priority ? t.priority.toUpperCase() : "Pending")),
                    rightStyle: { color: t.status === "completed" ? "var(--success)" : (t.priority === "high" ? "var(--danger)" : "var(--fg-muted)") },
                  }))}
                onClick={() => handleSetFilter("task")}
              />
            </div>
          </div>
        )}

        {/* HABITS */}
        {filter === "habit" && (
          <div>
            <div className="section-header">Habits ({habits.length} Active)</div>
            <div className="card" style={{ padding: 0 }}>
              {habits.length === 0 ? (
                <p className="text-muted text-sm" style={{ padding: 24 }}>No habits yet.</p>
              ) : (
                [...habits]
                  .sort((a, b) => (b.progress?.streak ?? 0) - (a.progress?.streak ?? 0))
                  .map((h) => {
                  const dh = daily?.habits?.find((item) => item.commitment.id === h.id);
                  const checked = !!dh?.today_record;
                  const itemLabels = h.labels || [];
                  const streak = h.progress?.streak ?? 0;
                  const days = streak % 7;
                  const weeks = Math.floor(streak / 7);

                  const habitRecords = (records || []).filter((r) => r.commitment_id === h.id && r.status === "done");
                  const checkinDates = habitRecords.map((r) => r.date);

                  return (
                    <div key={h.id} className="habit-item" style={{ padding: "16px 24px", display: "flex", alignItems: "center", borderBottom: "1px solid var(--border)" }}>
                      <div className="habit-left" style={{ display: "flex", alignItems: "center", gap: 12 }}>
                        <div
                          className={`checkbox${checked ? " checked" : ""}`}
                          onClick={() => handleHabitCheckIn(h.id, dh?.today_record?.id)}
                          style={{ cursor: "pointer" }}
                        />
                        <span
                          style={{ fontWeight: 500, color: "var(--fg)", cursor: "pointer" }}
                          onClick={() => setSelectedDetailId(h.id)}
                        >
                          {h.title}
                        </span>
                      </div>

                      <div style={{ flex: 1, marginLeft: 24, display: "flex", gap: 6, alignItems: "center", overflow: "visible" }}>
                        {itemLabels.map((lbl) => (
                          <LabelPill key={lbl.id || lbl.name} label={lbl} compact={itemLabels.length > 2} />
                        ))}
                      </div>

                      <div style={{ display: "flex", gap: 24, alignItems: "center" }}>
                        <InlineCalendar checkinDates={checkinDates} />
                        <div style={{ minWidth: 100, display: "flex", justifyContent: "flex-end" }}>
                          <span className="streak-badge" style={{ opacity: streak > 0 ? 1 : 0.5 }}>
                            🔥 {days}d {weeks}w
                          </span>
                        </div>
                        <button
                          className="icon-btn"
                          title="Edit"
                          onClick={() => setEditingCommitment(h)}
                          style={{ width: 32, height: 32 }}
                        >
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                          </svg>
                        </button>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        )}

        {/* GOALS */}
        {filter === "goal" && (
          <div>
            <div className="section-header">Goals ({goals.length} Active)</div>
            {goals.length === 0 ? (
              <p className="text-muted text-sm">No active goals.</p>
            ) : (
              <div className="dashboard-grid">
                {goals.map((g) => (
                  <GoalCard key={g.id} goal={g} showSubGoals onOpenDetail={(id) => setSelectedDetailId(id)} onEdit={(goal) => setEditingCommitment(goal)} />
                ))}
              </div>
            )}
          </div>
        )}

        {/* TASKS */}
        {filter === "task" && (
          <div>
            <div className="section-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span>Tasks ({tasks.length} Active)</span>
              <div style={{ fontSize: 12, display: "flex", gap: 12, fontWeight: 500, color: "var(--fg-muted)" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 6 }}><div className="priority-dot high" /> High</div>
                <div style={{ display: "flex", alignItems: "center", gap: 6 }}><div className="priority-dot med" /> Medium</div>
                <div style={{ display: "flex", alignItems: "center", gap: 6 }}><div className="priority-dot low" /> Low</div>
              </div>
            </div>
            <TaskGroupView tasks={tasks} todayISO={todayISO} onOpenDetail={(id) => setSelectedDetailId(id)} onEdit={(task) => setEditingCommitment(task)} onPromptReschedule={handlePromptReschedule} />
          </div>
        )}

      </div>

      {(showCreate || editingCommitment) && (
        <CreateCommitmentModal
          defaultType={createType}
          commitmentToEdit={editingCommitment}
          onClose={() => {
            setShowCreate(false);
            setEditingCommitment(null);
          }}
        />
      )}

      {selectedDetailId && (
        <CommitmentDetail
          commitmentId={selectedDetailId}
          onClose={() => setSelectedDetailId(null)}
          onEdit={(c) => setEditingCommitment(c)}
        />
      )}

      {rescheduleTaskId && (
        <RescheduleModal
          taskId={rescheduleTaskId}
          todayISO={todayISO}
          onClose={() => setRescheduleTaskId(null)}
          onConfirm={async (selectedDate) => {
            try {
              const payload = { due_date: selectedDate };
              if (clearParentIdOnReschedule) {
                payload.parent_id = null;
              }
              await updateCommitment(rescheduleTaskId, payload);
            } catch (err) {
              console.error("Failed to reschedule task:", err);
            }
            setRescheduleTaskId(null);
            setClearParentIdOnReschedule(false);
          }}
        />
      )}
    </div>
  );
}

// ── Summary Card ─────────────────────────────────────────────────────────

function SummaryCard({ icon, label, count, items, onClick }) {
  return (
    <div
      className="card"
      style={{ padding: 20, cursor: "pointer", transition: "transform 0.2s, border-color 0.2s" }}
      onMouseOver={(e) => { e.currentTarget.style.transform = "translateY(-2px)"; e.currentTarget.style.borderColor = "var(--fg-muted)"; }}
      onMouseOut={(e) => { e.currentTarget.style.transform = "none"; e.currentTarget.style.borderColor = "var(--border)"; }}
      onClick={onClick}
    >
      <h3 style={{ fontSize: 14, margin: "0 0 16px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span>{icon} {label}</span>
        <span className="text-xs text-muted" style={{ background: "var(--surface-raised)", padding: "2px 8px", borderRadius: 12 }}>
          {count} Active
        </span>
      </h3>
      <div style={{ display: "flex", flexDirection: "column", gap: 10, fontSize: 13 }}>
        {items.map((item, i) => (
          <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8, overflow: "visible", whiteSpace: "nowrap" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6, overflow: "visible", whiteSpace: "nowrap", flex: 1, minWidth: 0 }}>
              <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{item.left}</span>
              {(item.labels || []).map((lbl) => (
                <LabelPill key={lbl.id || lbl.name} label={lbl} compact={(item.labels || []).length > 2} />
              ))}
            </div>
            <span className="text-muted" style={{ whiteSpace: "nowrap", ...item.rightStyle }}>{item.right}</span>
          </div>
        ))}
        {count > items.length && (
          <div style={{ textAlign: "center", paddingTop: 4, opacity: 0.5 }}>
            + {count - items.length} more
          </div>
        )}
      </div>
    </div>
  );
}

// ── Task group view (Inbox / Today / Upcoming) ─────────────────────────

function TaskGroupView({ tasks, todayISO, onOpenDetail, onEdit, onPromptReschedule }) {
  const isCompletedToday = (t) => {
    if (t.status !== "completed" || !t.updated_at) return false;
    const d = new Date(t.updated_at);
    if (isNaN(d.getTime())) return false;
    const iso = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
    return iso === todayISO;
  };

  const getTwoWeeksLaterISO = (todayStr) => {
    const parts = todayStr.split("-");
    if (parts.length !== 3) return todayStr;
    const year = parseInt(parts[0], 10);
    const month = parseInt(parts[1], 10) - 1;
    const day = parseInt(parts[2], 10);
    const d = new Date(year, month, day);
    d.setDate(d.getDate() + 14);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  };
  const twoWeeksLaterISO = getTwoWeeksLaterISO(todayISO);

  const inbox = tasks.filter((t) => t.status !== "completed" && !t.due_date);
  const todayTasks = tasks.filter((t) =>
    (t.due_date && (t.due_date === todayISO || (t.due_date < todayISO && t.status !== "completed"))) ||
    isCompletedToday(t)
  );
  const upcoming = tasks.filter((t) => t.status !== "completed" && t.due_date && t.due_date > todayISO && t.due_date <= twoWeeksLaterISO);

  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 24 }}>
      <TaskColumn icon="📥" label="Inbox" tasks={inbox} todayISO={todayISO} onOpenDetail={onOpenDetail} onEdit={onEdit} onPromptReschedule={onPromptReschedule} />
      <TaskColumn icon="☀️" label="Today" tasks={todayTasks} todayISO={todayISO} onOpenDetail={onOpenDetail} onEdit={onEdit} onPromptReschedule={onPromptReschedule} />
      <TaskColumn icon="📅" label="Upcoming" tasks={upcoming} todayISO={todayISO} onOpenDetail={onOpenDetail} onEdit={onEdit} onPromptReschedule={onPromptReschedule} />
    </div>
  );
}

function TaskColumn({ icon, label, tasks, todayISO, onOpenDetail, onEdit, onPromptReschedule }) {
  const { createCommitment, updateCommitment } = usePursuitsStore();
  const [quickTitle, setQuickTitle] = useState("");
  const [showCompleted, setShowCompleted] = useState(true);
  const [isDragOver, setIsDragOver] = useState(false);
  const [dragOverTaskId, setDragOverTaskId] = useState(null);

  const PRIORITY_WEIGHT = { high: 3, medium: 2, med: 2, low: 1, none: 0 };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const taskId = e.dataTransfer.getData("text/plain");
    const sourceType = e.dataTransfer.getData("source-type");
    const sourceDueDate = e.dataTransfer.getData("source-due-date");
    
    if (sourceType === "task-card") {
      const shouldClearParent = false;
      
      if (label === "Today") {
        try {
          await updateCommitment(taskId, { due_date: todayISO, parent_id: null });
        } catch (err) {
          console.error("Failed to move task to Today:", err);
        }
      } else if (label === "Upcoming") {
        const isFromInbox = !sourceDueDate;
        const isFromToday = sourceDueDate === todayISO;
        
        if (isFromInbox || isFromToday || shouldClearParent) {
          onPromptReschedule?.(taskId, shouldClearParent);
        } else {
          // Already upcoming, keep existing or set tomorrow if somehow empty
          const tomorrow = new Date();
          tomorrow.setDate(tomorrow.getDate() + 1);
          const tomorrowISO = `${tomorrow.getFullYear()}-${String(tomorrow.getMonth() + 1).padStart(2, "0")}-${String(tomorrow.getDate()).padStart(2, "0")}`;
          const targetDate = sourceDueDate || tomorrowISO;
          try {
            await updateCommitment(taskId, { due_date: targetDate, parent_id: null });
          } catch (err) {
            console.error("Failed to move task to Upcoming:", err);
          }
        }
      } else if (label === "Inbox") {
        try {
          await updateCommitment(taskId, { due_date: null, parent_id: null });
        } catch (err) {
          console.error("Failed to move task to Inbox:", err);
        }
      }
    }
  };

  const handleTaskDragOver = (e, targetTask) => {
    if (targetTask.status === "completed") return;
    const dm = window.dragManager;
    if (!dm) return;

    if (dm.sourceType === "task-card" && dm.sourceColumn === String(label).toLowerCase()) {
      e.preventDefault();
      if (dragOverTaskId !== targetTask.id) {
        setDragOverTaskId(targetTask.id);
      }
    } else if (dm.sourceType === "task-card") {
      e.preventDefault();
    }
  };

  const handleTaskDragLeave = () => {
    setDragOverTaskId(null);
  };

  const handleTaskDrop = async (e, targetTask) => {
    const sourceType = e.dataTransfer.getData("source-type");
    if (sourceType !== "task-card") {
      // Let it bubble up to handleDrop of TaskColumn
      return;
    }

    const dragTaskId = e.dataTransfer.getData("text/plain");
    const dragTask = tasks.find(t => t.id === dragTaskId);
    if (!dragTask) {
      // It came from another column! Let it bubble up to TaskColumn's handleDrop!
      return;
    }

    e.preventDefault();
    e.stopPropagation();
    setDragOverTaskId(null);

    if (dragTaskId !== targetTask.id) {
      if (dragTask.status === "completed" || targetTask.status === "completed") return;

      const activeTasks = sortedTasks.filter(t => t.status !== "completed");
      const dragIndex = activeTasks.findIndex(t => t.id === dragTaskId);
      const targetIndex = activeTasks.findIndex(t => t.id === targetTask.id);

      if (dragIndex !== -1 && targetIndex !== -1) {
        const reordered = [...activeTasks];
        reordered.splice(dragIndex, 1);
        reordered.splice(targetIndex, 0, dragTask);

        const updates = reordered
          .map((t, i) => (t.sort_order !== i ? updateCommitment(t.id, { sort_order: i }) : null))
          .filter(Boolean);
        try {
          await Promise.all(updates);
        } catch (err) {
          console.error("Failed to update task sort order:", err);
        }
      }
    }
  };

  const filteredTasks = tasks.filter((t) => showCompleted || t.status !== "completed");

  const sortedTasks = [...filteredTasks].sort((a, b) => {
    const aDone = a.status === "completed";
    const bDone = b.status === "completed";
    if (aDone && !bDone) return 1;
    if (!aDone && bDone) return -1;
    if (aDone && bDone) {
      const timeA = new Date(a.updated_at || a.completed_at || 0).getTime();
      const timeB = new Date(b.updated_at || b.completed_at || 0).getTime();
      return timeB - timeA;
    }
    const orderA = a.sort_order ?? 0;
    const orderB = b.sort_order ?? 0;
    if (orderA !== orderB) return orderA - orderB;

    const weightA = PRIORITY_WEIGHT[a.priority?.toLowerCase()] ?? 0;
    const weightB = PRIORITY_WEIGHT[b.priority?.toLowerCase()] ?? 0;
    if (weightB !== weightA) {
      return weightB - weightA;
    }
    const createA = new Date(a.created_at || 0).getTime();
    const createB = new Date(b.created_at || 0).getTime();
    return createA - createB;
  });

  const handleToggle = async (task) => {
    const newStatus = task.status === "completed" ? "active" : "completed";
    const payload = { status: newStatus };
    await updateCommitment(task.id, payload);
  };

  const handleQuickAdd = async (e) => {
    if (e.key === "Enter" && quickTitle.trim()) {
      e.preventDefault();
      const title = quickTitle.trim();
      setQuickTitle("");
      const dueDate = label === "Today" ? todayISO : null;
      try {
        await createCommitment({
          title,
          type: "task",
          priority: "none",
          due_date: dueDate,
          status: "active",
        });
      } catch (err) {
        console.error("Failed to quick add task:", err);
      }
    }
  };

  return (
    <div
      className="card"
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      style={{
        border: isDragOver ? "2px dashed var(--accent)" : "1px solid var(--border)",
        boxShadow: isDragOver ? "0 0 0 4px var(--accent-glow)" : undefined,
        transition: "border var(--transition-fast), box-shadow var(--transition-fast)",
      }}
    >
      <h2 style={{ fontSize: 16, marginBottom: 16, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <span>{icon} {label}</span>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <button
            className="icon-btn"
            title={showCompleted ? "Hide done items" : "Show done items"}
            onClick={() => setShowCompleted(!showCompleted)}
            style={{ opacity: showCompleted ? 0.8 : 0.4, width: 24, height: 24 }}
          >
            {showCompleted ? (
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                <circle cx="12" cy="12" r="3" />
              </svg>
            ) : (
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                <line x1="1" y1="1" x2="23" y2="23" />
              </svg>
            )}
          </button>
          <span className="text-xs text-muted" style={{ background: "var(--surface-raised)", padding: "2px 8px", borderRadius: 12 }}>
            {tasks.length} items
          </span>
        </div>
      </h2>
      <div className="task-list">
        {sortedTasks.map((t) => (
          <div
            key={t.id}
            onDragOver={(e) => handleTaskDragOver(e, t)}
            onDragLeave={handleTaskDragLeave}
            onDrop={(e) => handleTaskDrop(e, t)}
            style={{
              borderTop: dragOverTaskId === t.id ? "2px solid var(--accent)" : "2px solid transparent",
              transition: "border-top 0.1s ease",
            }}
          >
            <TaskCard task={t} onToggleStatus={() => handleToggle(t)} onOpenDetail={onOpenDetail} onEdit={onEdit} />
          </div>
        ))}
        {tasks.length === 0 && <p className="text-muted text-sm">All clear ✓</p>}
        <div className="input-bar" style={{ marginTop: 12, paddingTop: 12, borderTop: "1px solid var(--border)" }}>
          <span style={{ opacity: 0.5 }}>+</span>
          <input
            type="text"
            value={quickTitle}
            onChange={(e) => setQuickTitle(e.target.value)}
            onKeyDown={handleQuickAdd}
            placeholder="Quick add..."
            style={{ border: "none", background: "transparent", width: "100%", outline: "none", fontSize: 14, color: "var(--fg)" }}
          />
        </div>
      </div>
    </div>
  );
}

function RescheduleModal({ taskId, onClose, onConfirm, todayISO }) {
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const tomorrowISO = `${tomorrow.getFullYear()}-${String(tomorrow.getMonth() + 1).padStart(2, "0")}-${String(tomorrow.getDate()).padStart(2, "0")}`;
  
  const [selectedDate, setSelectedDate] = useState(tomorrowISO);

  return (
    <div
      className="modal-backdrop"
      onClick={onClose}
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.4)",
        backdropFilter: "blur(4px)",
        zIndex: 1050,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <div
        className="modal-content"
        onClick={(e) => e.stopPropagation()}
        style={{
          background: "var(--surface-raised)",
          border: "1px solid var(--border-light)",
          borderRadius: "var(--radius-md)",
          padding: "24px",
          width: "320px",
          boxShadow: "0 20px 40px -15px rgba(0, 0, 0, 0.2)",
          display: "flex",
          flexDirection: "column",
          gap: "16px",
        }}
      >
        <h3 style={{ margin: 0, fontSize: "16px", fontWeight: 700, color: "var(--fg)" }}>Select Due Date</h3>
        
        <input
          type="date"
          value={selectedDate}
          min={tomorrowISO}
          onChange={(e) => setSelectedDate(e.target.value)}
          style={{
            width: "100%",
            padding: "10px 12px",
            borderRadius: "var(--radius-sm)",
            border: "1px solid var(--border-light)",
            background: "var(--bg)",
            color: "var(--fg)",
            fontSize: "14px",
            outline: "none",
            boxSizing: "border-box",
            fontFamily: "var(--font-main)"
          }}
        />

        <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "8px" }}>
          <button
            className="pill-btn"
            onClick={onClose}
            style={{ fontSize: "13px", padding: "6px 12px", background: "transparent", border: "1px solid var(--border)", color: "var(--fg)", cursor: "pointer" }}
          >
            Cancel
          </button>
          <button
            className="btn-primary"
            onClick={() => onConfirm(selectedDate)}
            style={{ fontSize: "13px", padding: "6px 16px", borderRadius: "16px", cursor: "pointer" }}
          >
            Schedule
          </button>
        </div>
      </div>
    </div>
  );
}

