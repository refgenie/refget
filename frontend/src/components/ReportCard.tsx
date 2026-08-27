import { useState } from 'react';
import { Icon } from './common/Icon';

export type ReportTone = 'info' | 'success' | 'warning' | 'danger';

interface ReportCardProps {
  title: string;
  /** Explanation shown on hovering the question mark. */
  tooltipText: string;
  messageArray: string[];
  colorScheme?: ReportTone;
}

const ReportCard = ({
  title,
  tooltipText,
  messageArray,
  colorScheme = 'info',
}: ReportCardProps) => {
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <div className={`report-card report-card--${colorScheme}`}>
      <div className='report-card__header'>
        <div className='flex items-center'>
          <span className='font-medium'>{title}</span>
          <span className='report-card__help'>
            <button
              type='button'
              className='btn--link ml-2'
              aria-label={`About ${title}`}
              onMouseEnter={() => setShowTooltip(true)}
              onMouseLeave={() => setShowTooltip(false)}
              onFocus={() => setShowTooltip(true)}
              onBlur={() => setShowTooltip(false)}
            >
              <Icon name='question' />
            </button>
            {showTooltip && <span className='report-card__tooltip'>{tooltipText}</span>}
          </span>
        </div>
      </div>

      <div className='report-card__body'>
        <ul className='mb-0 pl-4'>
          {messageArray.map((msg, index) => (
            <li key={index}>{msg}</li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export { ReportCard };
