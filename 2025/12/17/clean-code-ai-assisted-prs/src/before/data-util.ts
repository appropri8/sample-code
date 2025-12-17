// BEFORE: Helper soup - unrelated utility functions in one file
// Problems: no clear organization, generic names, mixed concerns

export function processData(input: any): any {
  const result = {};
  for (const item of input.items) {
    if (item.status === 'active') {
      result[item.id] = transformItem(item);
    }
  }
  return result;
}

export function transformItem(item: any): any {
  return {
    id: item.id,
    name: item.name,
    value: item.value * 1.1
  };
}

export function validateInput(data: any): boolean {
  if (!data) {
    return false;
  }
  if (!data.id) {
    return false;
  }
  if (!data.name) {
    return false;
  }
  return true;
}

export function calculateTotal(items: any[]): number {
  let total = 0;
  for (const item of items) {
    if (item && item.price) {
      total += item.price;
    }
  }
  return total;
}

export function formatDate(date: any): string {
  if (!date) {
    return '';
  }
  const d = new Date(date);
  return d.toISOString();
}

export function parseJson(json: string): any {
  try {
    return JSON.parse(json);
  } catch {
    return null;
  }
}
