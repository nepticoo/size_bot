const PERSIAN = "۰۱۲۳۴۵۶۷۸۹";
const ARABIC = "٠١٢٣٤٥٦٧٨٩";

export function toLatinDigits(text: string): string {
  return text.replace(/[۰-۹٠-٩]/g, (ch) => {
    const p = PERSIAN.indexOf(ch);
    if (p !== -1) return String(p);
    const a = ARABIC.indexOf(ch);
    if (a !== -1) return String(a);
    return ch;
  });
}

export function parseNumber(text: string): number {
  return parseFloat(toLatinDigits(text).trim().replace(/,/g, ""));
}

const LATIN_TO_PERSIAN: Record<string, string> = Object.fromEntries(
  "0123456789".split("").map((d, i) => [d, PERSIAN[i]])
);

export function toPersianDigits(value: string | number): string {
  return String(value).replace(/[0-9]/g, (d) => LATIN_TO_PERSIAN[d]);
}
