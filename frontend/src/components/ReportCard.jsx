import { useState } from 'react';

const ReportCard = ({
  title,
  tooltipText,
  messageArray,
  colorScheme = 'info'
}) => {
  const [showTooltip, setShowTooltip] = useState(false);

  // Map color scheme to Bootstrap CSS classes
  const headerClass = `bg-${colorScheme} bg-opacity-25`;
  const titleClass = `fw-medium text-${colorScheme}-emphasis`;
  const iconClass = `ms-2 text-${colorScheme}-emphasis`;
  const bodyClass = `bg-${colorScheme} bg-opacity-10 rounded-bottom-1`;

  return (
    <div
      className='card'
      style={{
        borderColor: 'var(--bs-border-color-translucent)',
      }}
    >
      <div
        className={`card-header ${headerClass}`}
        style={{
          borderColor: 'var(--bs-border-color-translucent)',
        }}
      >
        <div className='d-flex align-items-center'>
          <span className={titleClass}>
            {title}
          </span>
          <div className='position-relative'>
            <span
              className={iconClass}
              style={{
                width: '20px',
                height: '20px',
                fontSize: '0.7rem',
                cursor: 'pointer',
              }}
              onMouseEnter={() => setShowTooltip(true)}
              onMouseLeave={() => setShowTooltip(false)}
            >
              <i className='bi bi-question-circle-fill'></i>
            </span>
            {showTooltip && (
              <div
                className='position-absolute bg-dark text-white rounded p-2 shadow-lg'
                style={{
                  left: '25px',
                  top: '0',
                  width: '250px',
                  fontSize: '0.75rem',
                  zIndex: 1050,
                }}
              >
                {tooltipText}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className={`card-body ${bodyClass}`}>
        <ul className='mb-0'>
          {messageArray.map((msg, index) => (
            <li key={index}>{msg}</li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export { ReportCard };
