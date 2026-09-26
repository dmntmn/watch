import {
  CalendarOutlined,
  FileSearchOutlined,
  FolderOutlined,
  LogoutOutlined,
  TeamOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { Avatar, Dropdown, Layout, Menu, Space, theme, Typography } from 'antd';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '@/auth/useAuth';
import { usePermission } from '@/permissions';
import { useRealtime } from '@/realtime/useRealtime';

const { Sider, Header, Content } = Layout;

/** Основной каркас приложения: меню по правам, шапка с пользователем. */
export function AppLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const { can } = usePermission();
  const { token } = theme.useToken();

  // Live-обновления по Socket.IO (подключение на всё время сессии)
  useRealtime();

  const items = [
    { key: '/occupancy', icon: <CalendarOutlined />, label: 'Занятость' },
    { key: '/employees', icon: <TeamOutlined />, label: 'Сотрудники' },
    { key: '/projects', icon: <FolderOutlined />, label: 'Проекты' },
    ...(can('audit:read')
      ? [{ key: '/audit', icon: <FileSearchOutlined />, label: 'Аудит' }]
      : []),
  ];

  const fullName = [user?.lastName, user?.firstName].filter(Boolean).join(' ') || user?.email || '';

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider breakpoint="lg" collapsible>
        <div style={{ height: 56, display: 'grid', placeItems: 'center' }}>
          <Typography.Text strong style={{ color: '#fff' }}>
            Watch
          </Typography.Text>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={items}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            background: token.colorBgContainer,
            paddingInline: 24,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <Typography.Text strong>Учёт занятости работников</Typography.Text>
          <Space>
            <Typography.Text>{fullName}</Typography.Text>
            <Dropdown
              menu={{
                items: [
                  {
                    key: 'logout',
                    icon: <LogoutOutlined />,
                    label: 'Выйти',
                    onClick: logout,
                  },
                ],
              }}
            >
              <Avatar icon={<UserOutlined />} style={{ cursor: 'pointer' }} />
            </Dropdown>
          </Space>
        </Header>
        <Content style={{ padding: 24, background: token.colorBgLayout }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}