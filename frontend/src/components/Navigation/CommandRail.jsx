import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { CircleDot, FileText, Users, Mic, Settings } from 'lucide-react';
import styles from './CommandRail.module.css';

const NAV_ITEMS = [
  { path: '/app', icon: CircleDot, label: 'Command Hub' },
  { path: '/app/resume', icon: FileText, label: 'Resume Intelligence' },
  { path: '/app/interview', icon: Users, label: 'Interview Committee' },
  { path: '/app/voice', icon: Mic, label: 'Voice Studio' },
];

export default function CommandRail() {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <nav 
      className={`${styles.rail} ${isExpanded ? styles.expanded : ''}`}
      onMouseEnter={() => setIsExpanded(true)}
      onMouseLeave={() => setIsExpanded(false)}
    >
      <div className={styles.logo}>
        <div className={styles.logoIcon}>◈</div>
        {isExpanded && <div className={styles.logoText}>CAMPUSHIRE.AI</div>}
      </div>

      <div className={styles.divider} />

      <div className={styles.navItems}>
        {NAV_ITEMS.map(({ path, icon: Icon, label }) => (
          <NavLink
            key={path}
            to={path}
            end={path === '/app'}
            className={({ isActive }) => `${styles.navItem} ${isActive ? styles.active : ''}`}
          >
            <div className={styles.iconWrapper}>
              <Icon size={24} />
            </div>
            {isExpanded && <span className={styles.label}>{label}</span>}
          </NavLink>
        ))}
      </div>

      <div className={styles.bottomSection}>
        <div className={styles.divider} />
        <NavLink to="/app/settings" className={({ isActive }) => `${styles.navItem} ${isActive ? styles.active : ''}`}>
          <div className={styles.iconWrapper}><Settings size={24} /></div>
          {isExpanded && <span className={styles.label}>System</span>}
        </NavLink>
        <div className={styles.avatar}>
          <div className={styles.avatarInner}>G</div>
          {isExpanded && <span className={styles.label}>Goutham</span>}
        </div>
      </div>
    </nav>
  );
}
