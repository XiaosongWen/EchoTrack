import React, { useState } from "react";
import usePursuitsStore from "../../stores/pursuitsStore";
import LabelPicker from "./LabelPicker";
import EmojiPicker from "emoji-picker-react";

const TYPES = [
  { id: "habit", icon: "🔄", label: "Habit" },
  { id: "goal", icon: "🎯", label: "Goal" },
  { id: "task", icon: "📋", label: "Task" },
];

export default function CreateCommitmentModal({ defaultType = "habit", commitmentToEdit = null, onClose }) {
  const { createCommitment, updateCommitment, labels: storeLabels } = usePursuitsStore();

  const isEdit = !!commitmentToEdit;

  const [type, setType] = useState(commitmentToEdit?.type || defaultType || "habit");
  const [title, setTitle] = useState(commitmentToEdit?.title || "");
  const [icon, setIcon] = useState(commitmentToEdit?.config?.icon || "");
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const [description, setDescription] = useState(commitmentToEdit?.description || "");
  
  const initialLabels = (commitmentToEdit?.labels || []).map((l) => l.name);
  const [labels, setLabels] = useState(initialLabels);

  // Habit config
  const [targetCount, setTargetCount] = useState(commitmentToEdit?.config?.target_count || 7);

  // Goal config
  const [goalDeadline, setGoalDeadline] = useState(commitmentToEdit?.due_date || "");
  const [goalProgressType, setGoalProgressType] = useState(commitmentToEdit?.config?.progress_type || "checklist");
  const [goalTargetValue, setGoalTargetValue] = useState(commitmentToEdit?.config?.target_value || "");

  // Task config
  const [taskPriority, setTaskPriority] = useState(
    commitmentToEdit?.priority
      ? commitmentToEdit.priority.charAt(0).toUpperCase() + commitmentToEdit.priority.slice(1)
      : "None"
  );
  const [taskDueDate, setTaskDueDate] = useState(commitmentToEdit?.due_date || "");

  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim()) return;
    setSaving(true);

    const config = { 
      ...(commitmentToEdit?.config || {}),
      icon: icon || null
    };
    let priority = isEdit ? (commitmentToEdit.priority || "none") : "none";
    let due_date = isEdit ? commitmentToEdit.due_date : null;

    if (type === "habit") {
      config.target_count = Number(targetCount) || 7;
    } else if (type === "goal") {
      config.progress_type = goalProgressType;
      if (goalProgressType === "percentage") {
        config.target_value = Number(goalTargetValue) || 100;
      }
      due_date = goalDeadline || null;
    } else if (type === "task") {
      priority = taskPriority.toLowerCase();
      due_date = taskDueDate || null;
    }

    delete config.tags;

    const label_ids = labels
      .map((name) => storeLabels.find((l) => l.name.toLowerCase() === name.toLowerCase())?.id)
      .filter(Boolean);

    const payload = {
      title: title.trim(),
      description: description.trim() || null,
      type,
      priority,
      due_date,
      config,
      label_ids,
    };

    try {
      if (isEdit) {
        await updateCommitment(commitmentToEdit.id, payload);
      } else {
        await createCommitment({ ...payload, status: "active" });
      }
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
      onClose();
    }
  };

  return (
    <div
      id="create-modal-overlay"
      className="modal-overlay"
      style={{
        display: "flex",
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: "rgba(0, 0, 0, 0.5)",
        backdropFilter: "blur(4px)",
        zIndex: 1000,
        alignItems: "center",
        justifyContent: "center",
      }}
      onClick={onClose}
    >
      <div
        className="modal-card card"
        style={{
          width: "100%",
          maxWidth: "500px",
          maxHeight: "85vh",
          overflowY: "auto",
          padding: "32px",
          background: "var(--bg)",
          border: "1px solid var(--border)",
          boxShadow: "0 12px 32px rgba(0,0,0,0.2)",
          borderRadius: "12px",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
          <h2 id="modal-title" style={{ fontSize: "20px", fontWeight: "600", margin: 0 }}>
            {isEdit ? "Edit Commitment" : "Create New Commitment"}
          </h2>
          <button className="icon-btn" onClick={onClose} style={{ width: "32px", height: "32px" }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {/* Type Selection */}
          {!isEdit && (
            <div id="modal-type-selection">
              <p style={{ color: "var(--fg-muted)", marginBottom: "16px" }}>
                What kind of commitment would you like to create?
              </p>
            <div style={{ display: "flex", gap: "8px", marginBottom: "24px" }}>
              {TYPES.map((t) => {
                const isActive = type === t.id;
                return (
                  <button
                    key={t.id}
                    type="button"
                    className={`type-select-btn${isActive ? " active" : ""}`}
                    style={{
                      flex: 1,
                      padding: "12px 0",
                      borderRadius: "8px",
                      border: isActive ? "2px solid var(--accent)" : "1px solid var(--border)",
                      background: "var(--surface)",
                      cursor: "pointer",
                      display: "flex",
                      justifyContent: "center",
                      alignItems: "center",
                      gap: "6px",
                    }}
                    onClick={() => setType(t.id)}
                  >
                    <span style={{ fontSize: "16px" }}>{t.icon}</span>
                    <span style={{ fontWeight: "500", fontSize: "13px", color: "var(--fg)" }}>{t.label}</span>
                  </button>
                );
              })}
            </div>
          </div>
        )}

          {/* Name / Title */}
          <div>
            <label style={{ display: "block", fontSize: "13px", fontWeight: "500", marginBottom: "8px", color: "var(--fg-muted)" }}>
              Name
            </label>
            <div style={{ display: "flex", gap: "10px", alignItems: "center", position: "relative" }}>
              <div style={{ position: "relative" }}>
                <button
                  type="button"
                  style={{
                    width: "46px",
                    height: "46px",
                    borderRadius: "8px",
                    border: "1px solid var(--border)",
                    background: "var(--surface)",
                    fontSize: "20px",
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                  onClick={() => setShowEmojiPicker(!showEmojiPicker)}
                >
                  {icon || (TYPES.find((t) => t.id === type)?.icon || "📝")}
                </button>
                {showEmojiPicker && (
                  <div
                    style={{
                      position: "absolute",
                      top: "52px",
                      left: 0,
                      zIndex: 1010,
                      boxShadow: "0 8px 24px rgba(0,0,0,0.2)",
                      borderRadius: "8px",
                      overflow: "hidden",
                    }}
                  >
                    <EmojiPicker
                      theme="dark"
                      onEmojiClick={(emojiData) => {
                        setIcon(emojiData.emoji);
                        setShowEmojiPicker(false);
                      }}
                      width={320}
                      height={380}
                      skinTonesDisabled={true}
                    />
                  </div>
                )}
              </div>
              <input
                autoFocus
                id="modal-title-input"
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Read 10 pages a day"
                style={{
                  flex: 1,
                  padding: "12px 16px",
                  borderRadius: "8px",
                  border: "1px solid var(--border)",
                  background: "var(--surface)",
                  color: "var(--fg)",
                  fontSize: "14px",
                  outline: "none",
                  boxSizing: "border-box",
                }}
                required
              />
            </div>
          </div>

          {/* Description */}
          <div>
            <label style={{ display: "block", fontSize: "13px", fontWeight: "500", marginBottom: "8px", color: "var(--fg-muted)" }}>
              Description <span style={{ color: "var(--border)", fontWeight: "400" }}>(optional)</span>
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Add any details, notes, or criteria for success..."
              style={{
                width: "100%",
                padding: "12px 16px",
                borderRadius: "8px",
                border: "1px solid var(--border)",
                background: "var(--surface)",
                color: "var(--fg)",
                fontSize: "14px",
                outline: "none",
                boxSizing: "border-box",
                minHeight: "80px",
                resize: "vertical",
                fontFamily: "inherit",
              }}
            />
          </div>

          {/* LabelPicker Component */}
          <div>
            <label style={{ display: "block", fontSize: "13px", fontWeight: "500", marginBottom: "8px", color: "var(--fg-muted)" }}>
              Labels
            </label>
            <LabelPicker selectedLabels={labels} onChange={setLabels} />
          </div>

          {/* Dynamic Config Panels */}
          {type === "habit" && (
            <div id="config-habit" className="config-panel" style={{ display: "flex", gap: "16px" }}>
              <div style={{ flex: 1 }}>
                <label style={{ display: "block", fontSize: "13px", fontWeight: "500", marginBottom: "8px", color: "var(--fg-muted)" }}>
                  Target Count (per week)
                </label>
                <input
                  type="number"
                  value={targetCount}
                  onChange={(e) => setTargetCount(e.target.value)}
                  min="1"
                  max="7"
                  style={{
                    width: "100%",
                    padding: "12px 16px",
                    borderRadius: "8px",
                    border: "1px solid var(--border)",
                    background: "var(--surface)",
                    color: "var(--fg)",
                    fontSize: "14px",
                    outline: "none",
                    boxSizing: "border-box",
                  }}
                />
              </div>
            </div>
          )}

          {type === "goal" && (
            <div id="config-goal" className="config-panel" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              <div style={{ display: "flex", gap: "16px" }}>
                <div style={{ flex: 1 }}>
                  <label style={{ display: "block", fontSize: "13px", fontWeight: "500", marginBottom: "8px", color: "var(--fg-muted)" }}>
                    Deadline <span style={{ color: "var(--border)", fontWeight: "400" }}>(optional)</span>
                  </label>
                  <input
                    type="date"
                    value={goalDeadline}
                    onChange={(e) => setGoalDeadline(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "12px 16px",
                      borderRadius: "8px",
                      border: "1px solid var(--border)",
                      background: "var(--surface)",
                      color: "var(--fg-muted)",
                      fontSize: "14px",
                      outline: "none",
                      boxSizing: "border-box",
                      cursor: "pointer",
                    }}
                  />
                </div>
                <div style={{ flex: 1 }}>
                  <label style={{ display: "block", fontSize: "13px", fontWeight: "500", marginBottom: "8px", color: "var(--fg-muted)" }}>
                    Progress Type
                  </label>
                  <select
                    id="goal-progress-select"
                    value={goalProgressType}
                    onChange={(e) => setGoalProgressType(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "12px 16px",
                      borderRadius: "8px",
                      border: "1px solid var(--border)",
                      background: "var(--surface)",
                      color: "var(--fg)",
                      fontSize: "14px",
                      outline: "none",
                      cursor: "pointer",
                      boxSizing: "border-box",
                    }}
                  >
                    <option value="checklist">Checklist (Open-ended sub-tasks)</option>
                    <option value="percentage">Numeric Target (Known total)</option>
                  </select>
                  <div id="progress-helper-text" style={{ fontSize: "12px", color: "var(--fg-muted)", marginTop: "8px", lineHeight: 1.4 }}>
                    {goalProgressType === "checklist"
                      ? "Add sub-tasks as you go. 5/5 doesn't mean the goal is 100% complete if you plan to add more."
                      : "Track a known numeric target (e.g., 100 books) so you don't have to create 100 separate task rows."}
                  </div>
                </div>
              </div>

              {goalProgressType === "percentage" && (
                <div id="goal-percentage-fields" style={{ display: "flex" }}>
                  <div style={{ flex: 1 }}>
                    <label style={{ display: "block", fontSize: "13px", fontWeight: "500", marginBottom: "8px", color: "var(--fg-muted)" }}>
                      Target Value
                    </label>
                    <input
                      type="number"
                      value={goalTargetValue}
                      onChange={(e) => setGoalTargetValue(e.target.value)}
                      placeholder="e.g. 100"
                      style={{
                        width: "100%",
                        padding: "12px 16px",
                        borderRadius: "8px",
                        border: "1px solid var(--border)",
                        background: "var(--surface)",
                        color: "var(--fg)",
                        fontSize: "14px",
                        outline: "none",
                        boxSizing: "border-box",
                      }}
                    />
                  </div>
                </div>
              )}
            </div>
          )}

          {type === "task" && (
            <div id="config-task" className="config-panel" style={{ display: "flex", gap: "16px" }}>
              <div style={{ flex: 1 }}>
                <label style={{ display: "block", fontSize: "13px", fontWeight: "500", marginBottom: "8px", color: "var(--fg-muted)" }}>
                  Priority
                </label>
                <select
                  value={taskPriority}
                  onChange={(e) => setTaskPriority(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "12px 16px",
                    borderRadius: "8px",
                    border: "1px solid var(--border)",
                    background: "var(--surface)",
                    color: "var(--fg)",
                    fontSize: "14px",
                    outline: "none",
                    cursor: "pointer",
                    boxSizing: "border-box",
                  }}
                >
                  <option value="None">None</option>
                  <option value="Low">Low</option>
                  <option value="Medium">Medium</option>
                  <option value="High">High</option>
                </select>
              </div>
              <div style={{ flex: 1 }}>
                <label style={{ display: "block", fontSize: "13px", fontWeight: "500", marginBottom: "8px", color: "var(--fg-muted)" }}>
                  Due Date
                </label>
                <input
                  type="date"
                  value={taskDueDate}
                  onChange={(e) => setTaskDueDate(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "12px 16px",
                    borderRadius: "8px",
                    border: "1px solid var(--border)",
                    background: "var(--surface)",
                    color: "var(--fg-muted)",
                    fontSize: "14px",
                    outline: "none",
                    boxSizing: "border-box",
                    cursor: "pointer",
                  }}
                />
              </div>
            </div>
          )}

          {/* Footer Actions */}
          <div style={{ display: "flex", justifyContent: "flex-end", gap: "12px", marginTop: "32px" }}>
            <button
              type="button"
              style={{
                padding: "10px 20px",
                borderRadius: "8px",
                border: "none",
                background: "transparent",
                color: "var(--fg)",
                fontWeight: "500",
                cursor: "pointer",
              }}
              onClick={onClose}
            >
              Cancel
            </button>
            <button
              id="modal-submit-btn"
              type="submit"
              className="btn-primary"
              disabled={saving || !title.trim()}
              style={{ padding: "10px 24px", opacity: saving || !title.trim() ? 0.6 : 1 }}
            >
              {saving ? (isEdit ? "Saving..." : "Creating...") : (isEdit ? "Save Changes" : "Create")}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
