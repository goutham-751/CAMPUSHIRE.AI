import { Outlet } from 'react-router-dom';
import CommandRail from '../../components/Navigation/CommandRail';
import ContextHeader from '../../components/Navigation/ContextHeader';
import AmbientField from '../../components/Ambient/AmbientField';
import styles from './AppLayout.module.css';

export default function AppLayout() {
    return (
        <div className={styles.layout}>
            <AmbientField>
                <CommandRail />
                <div className={styles.main}>
                    <ContextHeader />
                    <main className={styles.content}>
                        <Outlet />
                    </main>
                </div>
            </AmbientField>
        </div>
    );
}
