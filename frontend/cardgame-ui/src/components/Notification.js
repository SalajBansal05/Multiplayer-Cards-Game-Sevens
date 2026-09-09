function Notification({ message, onClose }) {
  if (!message) return null;

  return (
    <div className="notification">
      <span>{message}</span>

      <button
        className="notification-close"
        onClick={onClose}
        aria-label="Dismiss notification"
      >
        ×
      </button>
    </div>
  );
}

export default Notification;