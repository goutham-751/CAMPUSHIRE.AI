import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from '../../components/Sidebar/Sidebar';
import TopNavbar from '../../components/TopNavbar/TopNavbar';
import './AppLayout.css';

const PAGE_TITLES = {
    '/app': 'Dashboard',
    '/app/resume': 'Resume Analyzer',
    '/app/interview': 'Mock Interview',
    '/app/voice': 'Voice Studio',
    '/app/settings': 'Settings',
};

export default function AppLayout() {
    const location = useLocation();
    const title = PAGE_TITLES[location.pathname] || 'CampusHire.AI';

    return (
        <div className="app-layout">
            <Sidebar />
            <div className="app-layout__main">
                <TopNavbar title={title} />
                <main className="app-layout__content">
                    <Outlet />
                </main>
            </div>
        </div>
    );
}
