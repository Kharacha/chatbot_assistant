import React, { useEffect, useMemo, useState } from "react";

type Message = {
    id: string;
    sender: "user" | "bot";
    text: string;
};

export const ChatWidget: React.FC = () => {
    const [businessId, setBusinessId] = useState<string>("");
    const [apiBaseUrl, setApiBaseUrl] = useState<string>("");
    const [sessionId, setSessionId] = useState<string | null>(null);

    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState<string>("");
    const [isSending, setIsSending] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Read query params once on mount
    useEffect(() => {
        const params = new URLSearchParams(window.location.search);

        const biz = params.get("businessId") ?? "demo-business";
        const api = params.get("apiBaseUrl") ?? "http://127.0.0.1:8000/api";

        setBusinessId(biz);
        setApiBaseUrl(api);
    }, []);

    const canSend = useMemo(
        () => !!businessId && !!apiBaseUrl && input.trim().length > 0 && !isSending,
        [businessId, apiBaseUrl, input, isSending]
    );

    const handleSend = async () => {
        if (!canSend) return;

        const userText = input.trim();
        setInput("");
        setError(null);

        const userMsg: Message = {
            id: crypto.randomUUID(),
            sender: "user",
            text: userText,
        };

        setMessages((prev) => [...prev, userMsg]);
        setIsSending(true);

        try {
            const resp = await fetch(`${apiBaseUrl}/chat/${businessId}`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    message: userText,
                    session_id: sessionId, // backend can treat null as "new session"
                }),
            });

            if (!resp.ok) {
                throw new Error(`HTTP ${resp.status}`);
            }

            const data = await resp.json();
            // Adjust these keys if your backend returns something slightly different
            const replyText: string = data.reply ?? data.answer ?? "No reply text.";
            const newSessionId: string | null = data.session_id ?? sessionId;

            if (newSessionId && newSessionId !== sessionId) {
                setSessionId(newSessionId);
            }

            const botMsg: Message = {
                id: crypto.randomUUID(),
                sender: "bot",
                text: replyText,
            };

            setMessages((prev) => [...prev, botMsg]);
        } catch (err: any) {
            console.error("Error calling chat API:", err);
            setError("Something went wrong talking to the server.");
            // Rollback last user message if you want, or leave it
        } finally {
            setIsSending(false);
        }
    };

    const handleKeyDown: React.KeyboardEventHandler<HTMLInputElement> = (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    // Basic Tailwind-styled widget
    return (
        <div className="min-h-screen flex items-center justify-center bg-slate-900">
            <div className="w-full max-w-md rounded-2xl shadow-lg bg-slate-950 border border-slate-800 flex flex-col overflow-hidden">
                <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between">
                    <div>
                        <h1 className="text-sm font-semibold text-white">
                            Website Assistant
                        </h1>
                        <p className="text-[11px] text-slate-400">
                            Business: <span className="font-mono">{businessId}</span>
                        </p>
                    </div>
                    <span className="px-2 py-1 rounded-full text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/40">
            Online
          </span>
                </div>

                <div className="flex-1 flex flex-col gap-2 p-3 overflow-y-auto bg-gradient-to-b from-slate-950 to-slate-900">
                    {messages.length === 0 && (
                        <div className="text-xs text-slate-400 text-center mt-6">
                            Ask anything about this business or its website.
                        </div>
                    )}
                    {messages.map((m) => (
                        <div
                            key={m.id}
                            className={`flex ${
                                m.sender === "user" ? "justify-end" : "justify-start"
                            }`}
                        >
                            <div
                                className={`max-w-[80%] rounded-2xl px-3 py-2 text-xs ${
                                    m.sender === "user"
                                        ? "bg-indigo-500 text-white"
                                        : "bg-slate-800 text-slate-50"
                                }`}
                            >
                                {m.text}
                            </div>
                        </div>
                    ))}
                    {error && (
                        <div className="text-[11px] text-red-400 text-center mt-2">
                            {error}
                        </div>
                    )}
                </div>

                <div className="border-t border-slate-800 px-3 py-2 bg-slate-950">
                    <div className="flex gap-2 items-center">
                        <input
                            className="flex-1 bg-slate-900 text-xs text-slate-100 rounded-xl px-3 py-2 outline-none border border-slate-700 focus:border-indigo-500"
                            placeholder="Type your question..."
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                        />
                        <button
                            onClick={handleSend}
                            disabled={!canSend}
                            className={`text-xs px-3 py-2 rounded-xl font-medium transition
              ${
                                canSend
                                    ? "bg-indigo-500 hover:bg-indigo-400 text-white"
                                    : "bg-slate-700 text-slate-400 cursor-not-allowed"
                            }`}
                        >
                            {isSending ? "..." : "Send"}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
