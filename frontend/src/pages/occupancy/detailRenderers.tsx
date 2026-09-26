import { DatePicker, Input, InputNumber, Select } from 'antd';
import dayjs from 'dayjs';
import type { ReactNode } from 'react';
import type { PeriodType } from '@/api/types';

export const PERIOD_TYPE_OPTIONS: Array<{ value: PeriodType; label: string }> = [
  { value: 'shift', label: 'Вахта' },
  { value: 'vacation', label: 'Отпуск' },
  { value: 'sick_leave', label: 'Больничный' },
  { value: 'flight', label: 'Перелёт' },
  { value: 'hotel', label: 'Гостиница' },
  { value: 'train', label: 'Поезд' },
  { value: 'taxi', label: 'Такси' },
  { value: 'other', label: 'Другое' },
];

export function periodTypeLabel(type: PeriodType): string {
  return PERIOD_TYPE_OPTIONS.find((o) => o.value === type)?.label ?? type;
}

export interface DetailFieldDef {
  name: string;
  label: string;
  kind: 'text' | 'textarea' | 'select' | 'datetime' | 'number';
  options?: Array<{ value: string; label: string }>;
  required?: boolean;
}

/** Поля деталей конкретного вида занятости (унифицированный реестр). */
export function detailFieldsFor(
  type: PeriodType,
  fieldOptions: Array<{ value: string; label: string }>,
): DetailFieldDef[] {
  switch (type) {
    case 'shift':
      return [
        {
          name: 'field_id',
          label: 'Месторождение',
          kind: 'select',
          required: true,
          options: fieldOptions,
        },
        { name: 'notes', label: 'Примечания', kind: 'textarea' },
      ];
    case 'flight':
      return [
        { name: 'airline', label: 'Авиакомпания', kind: 'text' },
        { name: 'flight_number', label: 'Номер рейса', kind: 'text' },
        { name: 'departure_airport', label: 'Аэропорт вылета', kind: 'text' },
        { name: 'arrival_airport', label: 'Аэропорт прилёта', kind: 'text' },
        { name: 'departure_at', label: 'Вылет', kind: 'datetime' },
        { name: 'arrival_at', label: 'Прилёт', kind: 'datetime' },
      ];
    case 'hotel':
      return [
        { name: 'hotel_name', label: 'Гостиница', kind: 'text' },
        { name: 'city', label: 'Город', kind: 'text' },
        { name: 'address', label: 'Адрес', kind: 'text' },
        { name: 'check_in_at', label: 'Заезд', kind: 'datetime' },
        { name: 'check_out_at', label: 'Выезд', kind: 'datetime' },
      ];
    case 'train':
      return [
        { name: 'route', label: 'Маршрут', kind: 'text' },
        { name: 'train_number', label: 'Номер поезда', kind: 'text' },
        { name: 'carriage', label: 'Вагон', kind: 'text' },
        { name: 'seat_number', label: 'Место', kind: 'text' },
        { name: 'departure_at', label: 'Отправление', kind: 'datetime' },
        { name: 'arrival_at', label: 'Прибытие', kind: 'datetime' },
      ];
    case 'taxi':
      return [
        { name: 'pickup_address', label: 'Откуда', kind: 'text' },
        { name: 'dropoff_address', label: 'Куда', kind: 'text' },
        { name: 'ride_at', label: 'Время поездки', kind: 'datetime' },
      ];
    case 'vacation':
    case 'sick_leave':
    case 'other':
    default:
      return [{ name: 'notes', label: 'Примечания', kind: 'textarea' }];
  }
}

/** Рендер компонента поля деталей. */
export function renderDetailField(def: DetailFieldDef): ReactNode {
  switch (def.kind) {
    case 'textarea':
      return <Input.TextArea rows={2} />;
    case 'select':
      return <Select options={def.options} placeholder="Выберите…" allowClear />;
    case 'datetime':
      return <DatePicker showTime format="DD.MM.YYYY HH:mm" style={{ width: '100%' }} />;
    case 'number':
      return <InputNumber style={{ width: '100%' }} />;
    default:
      return <Input />;
  }
}

/** Значения формы -> payload деталей (datetime в ISO). */
export function detailToPayload(
  values: Record<string, unknown>,
  type: PeriodType,
): Record<string, unknown> {
  const defs = detailFieldsFor(type, []);
  const payload: Record<string, unknown> = {};
  for (const def of defs) {
    const v = values[def.name];
    if (v === undefined || v === null || v === '') continue;
    payload[def.name] = def.kind === 'datetime' ? dayjs(v as string).toISOString() : v;
  }
  return payload;
}

/** Детали записи -> значения формы (ISO datetime -> dayjs). */
export function detailFromRecord(
  detail: Record<string, unknown> | null | undefined,
  type: PeriodType,
): Record<string, unknown> {
  const defs = detailFieldsFor(type, []);
  const values: Record<string, unknown> = {};
  if (!detail) return values;
  for (const def of defs) {
    const v = detail[def.name];
    if (v === undefined || v === null) continue;
    values[def.name] = def.kind === 'datetime' ? dayjs(String(v)) : v;
  }
  return values;
}