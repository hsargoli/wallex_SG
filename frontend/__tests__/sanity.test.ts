/**
 * Sanity test — verify Jest works + paper-format helpers.
 * Real assertions (not just truthy) — per Di Koyar.
 */
import { formatNum, parseNum, fmt, fmtNum } from "@/lib/paper-format";

describe("paper-format", () => {
  describe("formatNum (string → Latin commas)", () => {
    it("adds commas every 3 digits", () => {
      expect(formatNum("21686999673")).toBe("21,686,999,673");
    });

    it("strips non-digits then adds commas", () => {
      expect(formatNum("21,686,999,673")).toBe("21,686,999,673");
    });

    it("returns empty string on no digits", () => {
      expect(formatNum("abc")).toBe("");
      expect(formatNum("")).toBe("");
    });
  });

  describe("parseNum (string → digits only)", () => {
    it("strips Latin commas", () => {
      expect(parseNum("21,686,999,673")).toBe("21686999673");
    });

    it("strips Persian digits too (safety)", () => {
      // Persian digits are NOT in [0-9], so they get stripped.
      // This matches current behavior.
      expect(parseNum("۱۲۳۴")).toBe("");
    });

    it("returns empty on empty input", () => {
      expect(parseNum("")).toBe("");
    });
  });

  describe("fmt (number → Persian locale, rounded)", () => {
    it("returns '—' on null/undefined", () => {
      expect(fmt(null)).toBe("—");
      expect(fmt(undefined)).toBe("—");
    });

    it("rounds 1234.56 → 1235 in Persian", () => {
      // Per Node check: Math.round(1234.56).toLocaleString("fa-IR") === "۱٬۲۳۵"
      const result = fmt(1234.56);
      expect(result).toBe("۱٬۲۳۵");
    });

    it("renders 0", () => {
      const result = fmt(0);
      expect(result).toBe("۰");
    });

    it("does NOT return English digits", () => {
      const result = fmt(1234);
      expect(result).not.toBe("1234");
      expect(result).not.toBe("1,234");
      // Must contain Persian digit(s)
      expect(result).toMatch(/[۰-۹]/);
    });
  });
});

describe("fmtNum (Persian locale with decimals)", () => {
  it("returns '—' on null/undefined", () => {
    expect(fmtNum(null)).toBe("—");
    expect(fmtNum(undefined)).toBe("—");
  });

  it("formats 1234.56 with 2 digits", () => {
    expect(fmtNum(1234.56, 2)).toBe("۱٬۲۳۴٫۵۶");
  });

  it("rounds to given digits", () => {
    expect(fmtNum(1234.5678, 2)).toBe("۱٬۲۳۴٫۵۷");
  });

  it("no trailing zeros", () => {
    expect(fmtNum(1234, 2)).toBe("۱٬۲۳۴");
  });

  it("respects custom digits", () => {
    expect(fmtNum(45.678, 1)).toBe("۴۵٫۷");
  });
});
