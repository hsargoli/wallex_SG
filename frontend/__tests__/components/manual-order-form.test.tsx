/**
 * ManualOrderForm — Phase 2.5 features (RED first).
 *
 * 3 features extracted from /guest to bring parity:
 *  1. Price validation (✅/⚠️)
 *  2. 10-position cap (disabled + message)
 *  3. Variant-aware submit button text
 */
import { render, screen } from "@testing-library/react";
import { ManualOrderForm, type ManualOrderFormProps } from "@/components/paper-trading/manual-order-form";

const baseProps: ManualOrderFormProps = {
  isRunning: true,
  capital: 10_000_000,
  marketPrice: { data: { price: 21_000_000_000 }, isLoading: false },
  orderSymbol: "BTCTMN",
  orderAmount: "100000",
  orderTp: "2",
  orderSl: "1",
  orderLimitPrice: "",
  setOrderSymbol: jest.fn(),
  setOrderAmount: jest.fn(),
  setOrderTp: jest.fn(),
  setOrderSl: jest.fn(),
  setOrderLimitPrice: jest.fn(),
  onSubmit: jest.fn(),
  isSubmitting: false,
  variant: "user",
};

describe("ManualOrderForm (Phase 2.5)", () => {
  // ─── Feature 1: Price validation ─────────────────────────────
  describe("Price validation", () => {
    it("shows ⚠️ warning when limit_price < market_price", () => {
      render(<ManualOrderForm {...baseProps} orderLimitPrice="1000000" />);
      expect(screen.getByText(/⚠️/)).toBeInTheDocument();
      expect(screen.getByText(/قیمت شما < بازار/)).toBeInTheDocument();
    });

    it("shows ✅ when limit_price >= market_price", () => {
      render(<ManualOrderForm {...baseProps} orderLimitPrice="22000000000" />);
      expect(screen.getByText(/✅/)).toBeInTheDocument();
      expect(screen.getByText(/قیمت شما ≥ بازار/)).toBeInTheDocument();
    });

    it("shows no validation message when limit_price is empty", () => {
      render(<ManualOrderForm {...baseProps} orderLimitPrice="" />);
      expect(screen.queryByText(/قیمت شما.*بازار/)).not.toBeInTheDocument();
    });
  });

  // ─── Feature 2: 10-position cap ──────────────────────────────
  describe("10-position cap", () => {
    it("disables submit when openPositionsCount >= 10", () => {
      render(<ManualOrderForm {...baseProps} openPositionsCount={10} />);
      const btn = screen.getByRole("button", { name: /ثبت/ });
      expect(btn).toBeDisabled();
    });

    it("shows cap message when at 10 positions", () => {
      render(<ManualOrderForm {...baseProps} openPositionsCount={10} />);
      expect(screen.getByText(/سقف ۱۰ پوزیشن/)).toBeInTheDocument();
    });

    it("does NOT show cap message when under 10", () => {
      render(<ManualOrderForm {...baseProps} openPositionsCount={5} />);
      expect(screen.queryByText(/سقف ۱۰ پوزیشن/)).not.toBeInTheDocument();
    });
  });

  // ─── Feature 3: Variant-aware button text ────────────────────
  describe("Submit button text", () => {
    it("guest + running: 'ثبت خرید'", () => {
      render(<ManualOrderForm {...baseProps} variant="guest" />);
      expect(screen.getByRole("button", { name: /ثبت خرید/ })).toBeInTheDocument();
    });

    it("user + running: 'ثبت سفارش'", () => {
      render(<ManualOrderForm {...baseProps} variant="user" />);
      expect(screen.getByRole("button", { name: /ثبت سفارش/ })).toBeInTheDocument();
    });

    it("guest + not running: 'اول Paper را شروع کن'", () => {
      render(<ManualOrderForm {...baseProps} variant="guest" isRunning={false} />);
      expect(screen.getByText(/اول Paper را شروع کن/)).toBeInTheDocument();
    });

    it("submitting: 'در حال ثبت...'", () => {
      render(<ManualOrderForm {...baseProps} isSubmitting={true} />);
      expect(screen.getByRole("button", { name: /در حال ثبت/ })).toBeInTheDocument();
    });
  });
});
