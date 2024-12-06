export function PeriodTitles(index: number) {
  const titles = [
    "Full Game",
    "1st Half",
    "2nd Half",
    "Extra Time",
    "Extra Time 1st Half",
    "Extra Time 2nd Half",
    "Penalty Shootout"
  ];

  return titles[index];
}

export function setLocalStorage(key: string, value: any) {
  if (typeof window !== 'undefined') {
    localStorage.setItem(key, value);
  }
}

export function getLocalStorage(key: string) {
  if (typeof window !== 'undefined') {
    return localStorage.getItem(key);
  }
}
