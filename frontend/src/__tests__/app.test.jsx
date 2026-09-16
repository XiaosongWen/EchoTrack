import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";
import App from "../App";
import { useAuthStore } from "../stores/authStore";

vi.mock("../stores/usePursuitsStore", () => ({
  default: (selector) => {
    const state = {
      commitments: [],
      records: [],
      daily: null,
      loading: false,
      error: null,
      fetchCommitments: vi.fn(),
      fetchRecords: vi.fn(),
      fetchDaily: vi.fn(),
      createRecord: vi.fn(),
      checkInHabit: vi.fn(),
      uncheckHabit: vi.fn(),
    };
    return typeof selector === "function" ? selector(state) : state;
  },
}));

describe("App routing", () => {
  beforeEach(() => {
    useAuthStore.setState({
      user: { id: "test-user-id", email: "test@example.com" },
      session: { access_token: "mock-token" },
      loading: false,
      error: null,
      init: vi.fn(),
    });
  });

  it("renders login route when unauthenticated", () => {
    useAuthStore.setState({ user: null, session: null, loading: false });
    render(
      <MemoryRouter initialEntries={["/"]}>
        <App />
      </MemoryRouter>
    );
    expect(screen.getByRole("button", { name: "Sign In" })).toBeInTheDocument();
  });

  it("renders dashboard on the root route when authenticated", () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <App />
      </MemoryRouter>
    );
    // Dashboard renders the live clock container
    const clockContainer = document.querySelector(".flip-clock-container");
    expect(clockContainer).not.toBeNull();
  });

  it("renders Pursuits heading on /commitments", () => {
    render(
      <MemoryRouter initialEntries={["/commitments"]}>
        <App />
      </MemoryRouter>
    );
    expect(screen.getByRole("heading", { name: "Pursuits" })).toBeInTheDocument();
  });

  it("renders Knowledge heading on /knowledge", () => {
    render(
      <MemoryRouter initialEntries={["/knowledge"]}>
        <App />
      </MemoryRouter>
    );
    expect(screen.getByRole("heading", { name: "Knowledge" })).toBeInTheDocument();
  });

  it("renders sidebar alongside route content", () => {
    render(
      <MemoryRouter initialEntries={["/photos"]}>
        <App />
      </MemoryRouter>
    );
    expect(screen.getByText("EchoTrack")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Photos" })).toBeInTheDocument();
  });
});
