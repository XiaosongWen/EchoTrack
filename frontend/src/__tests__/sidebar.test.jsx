import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Sidebar from "../components/Sidebar";

describe("Sidebar", () => {
  it("renders the EchoTrack title", () => {
    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>
    );
    expect(screen.getByText("EchoTrack")).toBeInTheDocument();
  });

  it("renders all module navigation links", () => {
    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>
    );
    const expectedLabels = [
      "Dashboard",
      "Pursuits",
      "Photos",
      "Videos",
      "Books",
      "Knowledge",
    ];

    for (const label of expectedLabels) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
  });

  it("renders navigation links with correct hrefs", () => {
    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>
    );

    expect(screen.getByText("Dashboard").closest("a")).toHaveAttribute("href", "/");
    expect(screen.getByText("Pursuits").closest("a")).toHaveAttribute("href", "/commitments");
    expect(screen.getByText("Knowledge").closest("a")).toHaveAttribute("href", "/knowledge");
  });
});
