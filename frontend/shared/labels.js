// Единый справочник русских подписей для кодов из бэкенда (уровни, статусы и т.п.) — чтобы не разбрасывать их по разным компонентам, а держать в одном месте.
  const LEVEL = { beginner: 'Начинающий', intermediate: 'Средний', advanced: 'Продвинутый' };

  // Формат/тип занятия. Значения уточните по своим enum, если отличаются.
  const LESSON_FORMAT = { individual: 'Индивидуальный', group: 'Групповой', online: 'Онлайн' };
  const LESSON_TYPE   = { individual: 'Индивидуальное', group: 'Групповое', online: 'Онлайн' };

  const SESSION_STATUS = { scheduled: 'Запланировано', completed: 'Проведено', cancelled: 'Отменено' };
  const SUB_STATUS     = { active: 'Активен', expired: 'Истёк', used_up: 'Занятия закончились', cancelled: 'Отменён' };
  const EXAM_RESULT    = { pending: 'Ожидает', passed: 'Сдал', failed: 'Не сдал' };

  // Возвращает русскую подпись; для пустого значения — тире, для неизвестного — сам код.
  function pick(map) {
    return (code) => (code == null || code === '') ? '—' : (map[code] || code);
  }

  window.Labels = {
    level:         pick(LEVEL),
    lessonFormat:  pick(LESSON_FORMAT),
    lessonType:    pick(LESSON_TYPE),
    sessionStatus: pick(SESSION_STATUS),
    subStatus:     pick(SUB_STATUS),
    examResult:    pick(EXAM_RESULT),
    maps: { LEVEL, LESSON_FORMAT, LESSON_TYPE, SESSION_STATUS, SUB_STATUS, EXAM_RESULT },
  };
})();