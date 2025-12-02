import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import { ChatWidget } from "./ChatWidget";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
    <React.StrictMode>
        <ChatWidget />
    </React.StrictMode>
);
