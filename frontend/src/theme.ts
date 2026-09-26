import type { ThemeConfig } from 'antd';

/** Тема Ant Design v5 — минимализм, цвет через токены. */
export const themeConfig: ThemeConfig = {
  token: {
    colorPrimary: '#1677ff',
    borderRadius: 6,
    fontSize: 14,
  },
  components: {
    Layout: {
      siderBg: '#001529',
      headerBg: '#ffffff',
      headerHeight: 56,
    },
    Menu: {
      darkItemBg: '#001529',
      darkSubMenuItemBg: '#001529',
    },
  },
};