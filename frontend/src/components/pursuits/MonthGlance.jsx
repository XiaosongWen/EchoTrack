import React, { useMemo, useState } from "react";
import usePursuitsStore from "../../stores/pursuitsStore";

const WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

function buildCalendar(year, month) {
  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const cells = [];
  for (let i = 0; i < firstDay; i++) cells.push(null);
  for (let d = 1; d <= daysInMonth; d++) cells.push(d);
  while (cells.length % 7 !== 0) cells.push(null);
  return cells;
}

export default function MonthGlance({ habits = [] }) {
  const now = new Date();
  const [currentYear, setCurrentYear] = useState(now.getFullYear());
  const [currentMonth, setCurrentMonth] = useState(now.getMonth());
  const [selectedDateEvents, setSelectedDateEvents] = useState(null);
  const [dragOverDate, setDragOverDate] = useState(null);

  const todayDate = now.getDate();
  const isCurrentMonthYear = now.getFullYear() === currentYear && now.getMonth() === currentMonth;

  const { commitments, records, updateCommitment } = usePursuitsStore();

  const monthName = new Date(currentYear, currentMonth, 1).toLocaleString("default", { month: "long", year: "numeric" });

  const handlePrevMonth = () => {
    if (currentMonth === 0) {
      setCurrentMonth(11);
      setCurrentYear((y) => y - 1);
    } else {
      setCurrentMonth((m) => m - 1);
    }
  };

  const handleNextMonth = () => {
    if (currentMonth === 11) {
      setCurrentMonth(0);
      setCurrentYear((y) => y + 1);
    } else {
      setCurrentMonth((m) => m + 1);
    }
  };

  const handleToday = () => {
    const d = new Date();
    setCurrentYear(d.getFullYear());
    setCurrentMonth(d.getMonth());
  };

  // Group all items with dates by date string (YYYY-MM-DD)
  const eventsByDate = useMemo(() => {
    const map = {};
    const add = (dateStr, item) => {
      if (!dateStr) return;
      if (!map[dateStr]) map[dateStr] = [];
      map[dateStr].push(item);
    };

    // 1. Commitments with due_date
    (commitments || []).forEach((c) => {
      if (c.due_date) {
        const icon = c.config?.icon || (c.type === "task" ? "📋" : c.type === "goal" ? "🎯" : c.type === "habit" ? "🔄" : "📝");
        add(c.due_date, {
          id: `due-${c.id}`,
          title: c.title,
          type: c.type,
          priority: c.priority,
          timestamp: c.updated_at || c.completed_at || c.created_at,
          isDone: c.status === "completed",
          icon,
        });
      }
    });

    // 2. Completed commitments on their completion date if different from due_date
    (commitments || []).forEach((c) => {
      if (c.status === "completed") {
        const doneTime = c.updated_at || c.completed_at;
        if (doneTime) {
          const d = new Date(doneTime);
          if (!isNaN(d.getTime())) {
            const doneISO = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
            if (doneISO !== c.due_date) {
              add(doneISO, {
                id: `done-${c.id}`,
                title: c.title,
                type: c.type,
                priority: c.priority,
                timestamp: doneTime,
                isDone: true,
                icon: "✅",
              });
            }
          }
        }
      }
    });

    // 3. Habit check-in records
    (habits || []).forEach((h) => {
      if (h.today_record?.date) {
        if (!map[h.today_record.date]?.some((e) => e.id === `habit-${h.commitment.id}`)) {
          add(h.today_record.date, {
            id: `habit-${h.commitment.id}`,
            title: h.commitment.title,
            type: "habit",
            priority: h.commitment.priority,
            timestamp: h.today_record.created_at || h.today_record.updated_at,
            isDone: true,
            icon: h.commitment?.config?.icon || "🔄",
          });
        }
      }
    });

    return map;
  }, [commitments, habits]);

  const cells = useMemo(() => buildCalendar(currentYear, currentMonth), [currentYear, currentMonth]);

  // Compute habit dot status for a given date
  const getHabitDotStatus = (h, dateStr) => {
    // Never show dots for future dates — the habit hasn't happened yet
    const now = new Date();
    const todayISO = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
    if (dateStr > todayISO) return null;

    const createdStr = h.commitment?.created_at || h.created_at;
    if (createdStr) {
      const cd = new Date(createdStr);
      if (!isNaN(cd.getTime())) {
        const createdISO = `${cd.getFullYear()}-${String(cd.getMonth() + 1).padStart(2, "0")}-${String(cd.getDate()).padStart(2, "0")}`;
        if (dateStr < createdISO) {
          return null; // Habit did not exist yet on dateStr
        }
      }
    }

    const commitmentId = h.commitment?.id || h.id;
    const habitTitle = h.commitment?.title || h.title || "Habit";
    
    // Check-in on this date
    const checked = (records || []).some(
      (r) => r.commitment_id === commitmentId && r.date === dateStr && r.status === "done"
    ) || (h.today_record?.date === dateStr);

    if (checked) {
      return { color: "var(--success)", label: `${habitTitle}: Checked in`, icon: "🟢" };
    }

    const targetFreq = h.commitment?.config?.target_frequency || h.config?.target_frequency || 7;
    const d = new Date(dateStr);
    const dayOfWeek = (d.getDay() + 6) % 7; // 0 = Mon, 6 = Sun
    const monday = new Date(d);
    monday.setDate(d.getDate() - dayOfWeek);
    const sunday = new Date(monday);
    sunday.setDate(monday.getDate() + 6);

    const checkinsInWeek = (records || []).filter((r) => {
      if (r.commitment_id !== commitmentId || r.status !== "done") return false;
      const rd = new Date(r.date);
      return rd >= monday && rd <= sunday;
    }).length;

    const remainingDaysInWeek = 6 - dayOfWeek;
    const canReachTarget = (checkinsInWeek + remainingDaysInWeek) >= targetFreq;

    if (checkinsInWeek >= targetFreq || canReachTarget) {
      return { color: "var(--warning)", label: `${habitTitle}: Not checked in (streak safe)`, icon: "🟡" };
    }
    return { color: "var(--danger)", label: `${habitTitle}: Not checked in (streak broken)`, icon: "🔴" };
  };

  const handleEventDragStart = (e, ev, sourceDateStr) => {
    const actualId = ev.id.replace(/^(due-|done-|habit-)/, "");
    e.dataTransfer.setData("text/plain", actualId);
    e.dataTransfer.setData("source-type", "calendar-event");
    e.dataTransfer.setData("source-date", sourceDateStr);
    
    window.dragManager = {
      draggedItemId: actualId,
      sourceType: "calendar-event",
      sourceParentId: null,
      sourceColumn: null,
      sourceDate: sourceDateStr
    };
  };

  const handleEventDragEnd = () => {
    window.dragManager = null;
  };

  const handleCellDragOver = (e, dateStr) => {
    const dm = window.dragManager;
    if (!dm || dm.sourceType !== "calendar-event") return;
    if (dm.sourceDate === dateStr) return;
    e.preventDefault();
    if (dragOverDate !== dateStr) {
      setDragOverDate(dateStr);
    }
  };

  const handleCellDragLeave = () => {
    setDragOverDate(null);
  };

  const handleCellDrop = async (e, dateStr) => {
    e.preventDefault();
    setDragOverDate(null);

    const dm = window.dragManager;
    if (!dm || dm.sourceType !== "calendar-event") return;
    if (dm.sourceDate === dateStr) return;

    const commitmentId = dm.draggedItemId;
    try {
      await updateCommitment(commitmentId, { due_date: dateStr });
    } catch (err) {
      console.error("Failed to update commitment due date:", err);
    }

    setSelectedDateEvents(null);
  };

  const handleCellClick = (day) => {
    if (!day) return;
    const dateStr = `${currentYear}-${String(currentMonth + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    const d = new Date(currentYear, currentMonth, day);
    const formattedDate = d.toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric", year: "numeric" });
    
    const PRIORITY_WEIGHT = { high: 3, medium: 2, med: 2, low: 1, none: 0 };
    const rawEvents = eventsByDate[dateStr] || [];
    
    const pendingEvents = rawEvents
      .filter((e) => !e.isDone)
      .sort((a, b) => {
        const weightA = PRIORITY_WEIGHT[a.priority?.toLowerCase()] ?? 0;
        const weightB = PRIORITY_WEIGHT[b.priority?.toLowerCase()] ?? 0;
        if (weightB !== weightA) return weightB - weightA;
        return new Date(a.timestamp || 0).getTime() - new Date(b.timestamp || 0).getTime();
      });

    const doneEvents = rawEvents
      .filter((e) => e.isDone)
      .sort((a, b) => new Date(b.timestamp || 0).getTime() - new Date(a.timestamp || 0).getTime());

    setSelectedDateEvents({ dateStr, formattedDate, pendingEvents, doneEvents });
  };

  const allHabits = habits.length > 0 ? habits : (commitments || []).filter((c) => c.type === "habit");

  return (
    <div className="month-glance" style={{ marginTop: "32px" }}>
      <div className="month-header-wrapper">
        <h2 style={{ fontSize: "18px", fontWeight: 600, margin: 0, color: "var(--fg)" }}>
          {monthName}
        </h2>
        <div style={{ display: "flex", gap: "4px", alignItems: "center" }}>
          <button className="icon-btn" style={{ width: 28, height: 28 }} onClick={handlePrevMonth} title="Previous Month">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M15 18l-6-6 6-6" />
            </svg>
          </button>
          <button className="pill-btn" style={{ fontSize: 13, padding: "4px 12px" }} onClick={handleToday}>
            Today
          </button>
          <button className="icon-btn" style={{ width: 28, height: 28 }} onClick={handleNextMonth} title="Next Month">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 18l6-6-6-6" />
            </svg>
          </button>
        </div>
      </div>

      {WEEKDAYS.map((d) => (
        <div key={d} className="weekday-header">{d}</div>
      ))}

      {cells.map((day, i) => {
        if (!day) return <div key={`e${i}`} className="day-cell empty"><span className="day-number" /></div>;

        const dateStr = `${currentYear}-${String(currentMonth + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
        const isToday = isCurrentMonthYear && day === todayDate;
        const dayEvents = eventsByDate[dateStr] || [];
        const pendingDayEvents = dayEvents.filter((ev) => !ev.isDone);

        return (
          <div
            key={day}
            className={`day-cell${isToday ? " active" : ""}`}
            style={{
              cursor: "pointer",
              borderColor: dragOverDate === dateStr ? "var(--accent)" : undefined,
              background: dragOverDate === dateStr ? "var(--accent-glow)" : undefined,
              boxShadow: dragOverDate === dateStr ? "0 0 0 2px var(--accent)" : undefined,
            }}
            onClick={() => handleCellClick(day)}
            onDragOver={(e) => handleCellDragOver(e, dateStr)}
            onDragLeave={handleCellDragLeave}
            onDrop={(e) => handleCellDrop(e, dateStr)}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span className="day-number">{day}</span>
              {allHabits.length > 0 && (
                <div style={{ display: "flex", alignItems: "center", gap: 3 }}>
                  {allHabits.map((h, idx) => {
                    const status = getHabitDotStatus(h, dateStr);
                    if (!status) return null;
                    return (
                      <div
                        key={h.id || h.commitment?.id || idx}
                        title={status.label}
                        style={{
                          width: 6,
                          height: 6,
                          borderRadius: "50%",
                          background: status.color,
                          boxShadow: `0 0 3px ${status.color}`,
                        }}
                      />
                    );
                  })}
                </div>
              )}
            </div>

            {pendingDayEvents.length > 0 && (
              <div
                className="day-events-list"
                style={{ display: "flex", flexDirection: "column", gap: 3, marginTop: 4, overflow: "hidden" }}
                title={pendingDayEvents.map((ev) => `${ev.icon} ${ev.title}`).join("\n")}
              >
                {pendingDayEvents.slice(0, 3).map((ev) => (
                  <div
                    key={ev.id}
                    className="day-event"
                    draggable={true}
                    onDragStart={(e) => handleEventDragStart(e, ev, dateStr)}
                    onDragEnd={handleEventDragEnd}
                    style={{
                      fontSize: 10,
                      padding: "2px 4px",
                      borderRadius: 4,
                      background: "var(--surface-raised)",
                      color: "var(--fg)",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                      display: "flex",
                      alignItems: "center",
                      gap: 4,
                      cursor: "grab",
                    }}
                  >
                    <span style={{ fontSize: 10 }}>{ev.icon}</span>
                    <span>{ev.title}</span>
                  </div>
                ))}
                {pendingDayEvents.length > 3 && (
                  <span style={{ fontSize: 9, opacity: 0.6, color: "var(--fg-muted)", paddingLeft: 2 }}>
                    +{pendingDayEvents.length - 3} more
                  </span>
                )}
              </div>
            )}
          </div>
        );
      })}

      {/* Date Events Modal Popup */}
      {selectedDateEvents && (
        <div
          className="modal-overlay"
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0, 0, 0, 0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
            backdropFilter: "blur(4px)",
          }}
          onClick={() => setSelectedDateEvents(null)}
        >
          <div
            className="card"
            style={{
              width: 440,
              maxWidth: "92vw",
              maxHeight: "85vh",
              overflowY: "auto",
              padding: 24,
              background: "var(--surface)",
              boxShadow: "0 8px 32px rgba(0, 0, 0, 0.3)",
              borderRadius: "var(--radius-md)",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* 1. First line: Date */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
              <h3 style={{ fontSize: 16, fontWeight: 600, margin: 0, color: "var(--fg)" }}>
                📅 {selectedDateEvents.formattedDate}
              </h3>
              <button
                className="icon-btn"
                style={{ width: 28, height: 28, fontSize: 16 }}
                onClick={() => setSelectedDateEvents(null)}
              >
                ✕
              </button>
            </div>

            {/* 2. Second line: Habit Status Dots */}
            {allHabits.length > 0 && (
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
                {allHabits.map((h, idx) => {
                  const status = getHabitDotStatus(h, selectedDateEvents.dateStr);
                  if (!status) return null;
                  return (
                    <div
                      key={h.id || h.commitment?.id || idx}
                      title={status.label}
                      style={{
                        width: 10,
                        height: 10,
                        borderRadius: "50%",
                        background: status.color,
                        boxShadow: `0 0 4px ${status.color}`,
                        cursor: "pointer",
                      }}
                    />
                  );
                })}
              </div>
            )}

            {/* 3. Third section: Pending Items */}
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: "var(--fg-muted)", marginBottom: 8 }}>
                Pending Items ({selectedDateEvents.pendingEvents.length})
              </div>
              {selectedDateEvents.pendingEvents.length === 0 ? (
                <p className="text-muted text-xs" style={{ fontStyle: "italic", opacity: 0.7, margin: 0 }}>
                  No pending items for this date.
                </p>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  {selectedDateEvents.pendingEvents.map((ev) => (
                    <div
                      key={ev.id}
                      draggable={true}
                      onDragStart={(e) => handleEventDragStart(e, ev, selectedDateEvents.dateStr)}
                      onDragEnd={handleEventDragEnd}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 10,
                        padding: "8px 12px",
                        borderRadius: 6,
                        background: "var(--surface-raised)",
                        border: "1px solid var(--border)",
                        cursor: "grab",
                      }}
                    >
                      <span style={{ fontSize: 16 }}>{ev.icon}</span>
                      <span style={{ flex: 1, fontWeight: 500, fontSize: 13, color: "var(--fg)" }}>{ev.title}</span>
                      <span className="text-xs text-muted" style={{ textTransform: "capitalize" }}>{ev.type}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* 4. Fourth section: Done Items (Sorted by Done Time) */}
            <div>
              <div style={{ fontSize: 13, fontWeight: 600, color: "var(--fg-muted)", marginBottom: 8 }}>
                Done Items ({selectedDateEvents.doneEvents.length})
              </div>
              {selectedDateEvents.doneEvents.length === 0 ? (
                <p className="text-muted text-xs" style={{ fontStyle: "italic", opacity: 0.7, margin: 0 }}>
                  No done items recorded for this date.
                </p>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  {selectedDateEvents.doneEvents.map((ev) => {
                    const doneTimeStr = ev.timestamp
                      ? new Date(ev.timestamp).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false })
                      : "Done";
                    return (
                      <div
                        key={ev.id}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 10,
                          padding: "8px 12px",
                          borderRadius: 6,
                          background: "rgba(46, 160, 67, 0.1)",
                          border: "1px solid rgba(46, 160, 67, 0.2)",
                        }}
                      >
                        <span style={{ fontSize: 16 }}>{ev.icon}</span>
                        <span style={{ flex: 1, fontWeight: 500, fontSize: 13, color: "var(--fg)", textDecoration: "line-through" }}>
                          {ev.title}
                        </span>
                        <span className="log-time" style={{ fontSize: 11 }}>{doneTimeStr}</span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
