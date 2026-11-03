import "@testing-library/jest-dom/vitest";

import { afterAll, afterEach, beforeAll } from "vitest";

import { _reiniciar as reiniciarDescanso } from "./src/lib/descanso";
import { servidor } from "./src/test/servidor";

beforeAll(() =>
  servidor.listen({ onUnhandledRequest: "error" }),
);
afterEach(() => {
  servidor.resetHandlers();
  reiniciarDescanso();
});
afterAll(() => servidor.close());

HTMLDialogElement.prototype.showModal = function () { this.setAttribute("open", ""); };
HTMLDialogElement.prototype.close = function () { this.removeAttribute("open"); };
