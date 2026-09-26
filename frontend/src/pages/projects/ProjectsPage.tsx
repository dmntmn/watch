import { App, Button, Input, Modal, Space, Table } from 'antd';
import { PlusOutlined, ReloadOutlined, SearchOutlined, TeamOutlined } from '@ant-design/icons';
import { useMemo, useState } from 'react';
import type { Field, Project } from '@/api/types';
import { apiErrorMessage } from '@/api/client';
import { ConfirmDeleteButton } from '@/components/ConfirmDeleteButton';
import { PageHeader } from '@/components/PageHeader';
import { PermissionGate } from '@/components/PermissionGate';
import { EmptyState, ErrorState, LoadingState } from '@/components/States';
import {
  useCreateField,
  useDeleteField,
  useDeleteProject,
  useProjectFields,
  useProjects,
  useUpdateField,
} from '@/hooks/queries';
import { usePermission } from '@/permissions';
import { AssignmentDrawer } from './AssignmentDrawer';
import { ProjectFormModal } from './ProjectFormModal';

function FieldsBlock({ projectId }: { projectId: string }) {
  const { can } = usePermission();
  const { message } = App.useApp();
  const { data, isLoading } = useProjectFields(projectId);
  const createMutation = useCreateField(projectId);
  const updateMutation = useUpdateField();
  const deleteMutation = useDeleteField(projectId);
  const [newName, setNewName] = useState('');
  const [editing, setEditing] = useState<Field | null>(null);

  const handleCreate = async () => {
    if (!newName.trim()) return;
    try {
      await createMutation.mutateAsync({ name: newName.trim() });
      message.success('Месторождение добавлено');
      setNewName('');
    } catch (error) {
      message.error(apiErrorMessage(error));
    }
  };

  const handleRename = async () => {
    if (!editing) return;
    try {
      await updateMutation.mutateAsync({ id: editing.id, data: { name: editing.name } });
      message.success('Месторождение обновлено');
      setEditing(null);
    } catch (error) {
      message.error(apiErrorMessage(error));
    }
  };

  if (isLoading) return <LoadingState rows={2} />;

  return (
    <div style={{ maxWidth: 640 }}>
      {can('projects:manage') && (
        <Space style={{ marginBottom: 12 }}>
          <Input
            placeholder="Название месторождения"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onPressEnter={() => void handleCreate()}
          />
          <Button type="primary" disabled={!newName.trim()} onClick={() => void handleCreate()}>
            Добавить
          </Button>
        </Space>
      )}
      <Table<Field>
        rowKey="id"
        size="small"
        dataSource={data ?? []}
        pagination={false}
        loading={false}
        locale={{ emptyText: 'Месторождений нет' }}
        columns={[
          { title: 'Месторождение', dataIndex: 'name' },
          ...(can('projects:manage')
            ? [
                {
                  title: '',
                  key: 'actions',
                  render: (_: unknown, f: Field) => (
                    <Space size={4}>
                      <Button size="small" type="link" onClick={() => setEditing(f)}>
                        Переименовать
                      </Button>
                      <ConfirmDeleteButton
                        size="small"
                        title="Удалить месторождение?"
                        onConfirm={async () => {
                          await deleteMutation.mutateAsync(f.id);
                          message.success('Месторождение удалено');
                        }}
                      />
                    </Space>
                  ),
                },
              ]
            : []),
        ]}
      />
      <Modal
        open={Boolean(editing)}
        title="Переименовать месторождение"
        onOk={() => void handleRename()}
        onCancel={() => setEditing(null)}
        okText="Сохранить"
        cancelText="Отмена"
      >
        <Input
          value={editing?.name ?? ''}
          onChange={(e) =>
            setEditing((prev) => (prev ? { ...prev, name: e.target.value } : prev))
          }
        />
      </Modal>
    </div>
  );
}

export default function ProjectsPage() {
  const { can } = usePermission();
  const { message } = App.useApp();
  const { data, isLoading, isError, refetch } = useProjects();
  const deleteMutation = useDeleteProject();
  const [search, setSearch] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Project | null>(null);
  const [drawerProject, setDrawerProject] = useState<Project | null>(null);

  const filtered = useMemo(() => {
    if (!data) return [];
    const q = search.trim().toLowerCase();
    if (!q) return data;
    return data.filter(
      (p) => p.name.toLowerCase().includes(q) || (p.description ?? '').toLowerCase().includes(q),
    );
  }, [data, search]);

  if (isLoading) return <LoadingState />;
  if (isError)
    return <ErrorState error="Не удалось загрузить проекты" onRetry={() => void refetch()} />;

  return (
    <>
      <PageHeader
        title="Проекты"
        extra={
          <Space>
            <Input
              allowClear
              prefix={<SearchOutlined />}
              placeholder="Поиск по названию"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ width: 240 }}
            />
            <Button icon={<ReloadOutlined />} onClick={() => void refetch()} />
            <PermissionGate action="projects:manage">
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => {
                  setEditing(null);
                  setModalOpen(true);
                }}
              >
                Добавить
              </Button>
            </PermissionGate>
          </Space>
        }
      />
      {!filtered.length ? (
        <EmptyState description="Проекты не найдены" />
      ) : (
        <Table<Project>
          rowKey="id"
          dataSource={filtered}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (t) => `Всего: ${t}`,
          }}
          columns={[
            {
              title: 'Название',
              dataIndex: 'name',
              sorter: (a, b) => a.name.localeCompare(b.name),
            },
            {
              title: 'Описание',
              dataIndex: 'description',
              render: (v: string | null) => v ?? '—',
            },
            {
              title: '',
              key: 'actions',
              render: (_: unknown, p: Project) => (
                <Space size={4}>
                  <Button
                    type="link"
                    size="small"
                    icon={<TeamOutlined />}
                    onClick={() => setDrawerProject(p)}
                  >
                    Сотрудники
                  </Button>
                  {can('projects:manage') && (
                    <>
                      <Button
                        type="link"
                        size="small"
                        onClick={() => {
                          setEditing(p);
                          setModalOpen(true);
                        }}
                      >
                        Изменить
                      </Button>
                      <ConfirmDeleteButton
                        size="small"
                        title="Удалить проект?"
                        description="Месторождения и назначения проекта будут удалены."
                        onConfirm={async () => {
                          await deleteMutation.mutateAsync(p.id);
                          message.success('Проект удалён');
                        }}
                      />
                    </>
                  )}
                </Space>
              ),
            },
          ]}
          expandable={{
            expandedRowRender: (p) => <FieldsBlock projectId={p.id} />,
          }}
        />
      )}
      <ProjectFormModal open={modalOpen} project={editing} onClose={() => setModalOpen(false)} />
      <AssignmentDrawer
        projectId={drawerProject?.id ?? ''}
        projectName={drawerProject?.name ?? ''}
        open={Boolean(drawerProject)}
        onClose={() => setDrawerProject(null)}
      />
    </>
  );
}