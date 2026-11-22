import { useEffect } from 'react';
import { AlertTriangle, X } from 'lucide-react';

export default function RedAlertModal({ open, onClose }) {
  useEffect(() => {
    if (!open) return undefined;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const handleKeyDown = (event) => {
      if (event.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="red-alert-backdrop">
      <section
        className="red-alert-modal"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="red-alert-title"
        aria-describedby="red-alert-description"
      >
        <button
          type="button"
          className="red-alert-close"
          onClick={onClose}
          aria-label="Close red alert"
          title="Close"
        >
          <X size={22} />
        </button>

        <div className="red-alert-symbol">
          <AlertTriangle size={30} strokeWidth={2.4} />
        </div>
        <span className="red-alert-eyebrow">IMMEDIATE ACTION REQUIRED</span>
        <h2 id="red-alert-title">RED ALERT</h2>
        <p id="red-alert-description">
          RED ALERT, Evacuate to a nearest safe location
        </p>
        <span className="red-alert-footnote">
          Follow local emergency instructions and move away from the affected area.
        </span>
      </section>
    </div>
  );
}
