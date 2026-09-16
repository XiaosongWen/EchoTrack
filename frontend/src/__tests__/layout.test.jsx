import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Layout from "../components/Layout";

describe("Layout", () => {
  it("renders the sidebar alongside children", () => {
    render(
      <MemoryRouter>
        <Layout>
          <p>Page content</p>
        </Layout>
      </MemoryRouter>
    );

    // Sidebar title visible
    expect(screen.getByText("EchoTrack")).toBeInTheDocument();

    // Children rendered
    expect(screen.getByText("Page content")).toBeInTheDocument();
  });

  it("wraps children inside a main element", () => {
    render(
      <MemoryRouter>
        <Layout>
          <p>Hello</p>
        </Layout>
      </MemoryRouter>
    );

    const container = screen.getByText("Hello").closest(".main-container");
    expect(container).toBeInTheDocument();
  });
});
