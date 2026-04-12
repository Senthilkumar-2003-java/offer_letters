import { useState, useEffect, useRef } from "react";
import axios from "axios";

const API = "http://127.0.0.1:8000/api";

const C = {
  primary:  "#1a237e",
  light:    "#e8eaf6",
  accent:   "#5c6bc0",
  success:  "#2e7d32",
  error:    "#c62828",
  border:   "#c5cae9",
  text:     "#212121",
  muted:    "#757575",
  white:    "#ffffff",
  bg:       "#f5f6ff",
  appt:     "#1b5e20",
  joining:  "#bf360c",
  contract: "#4a148c",
};

/* ─── Input ──────────────────────────────────────────────────────────────── */
const Input = ({ label, ...props }) => (
  <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
    {label && <label style={{ fontSize: 12, color: C.muted, fontWeight: 600 }}>{label}</label>}
    <input
      {...props}
      style={{
        padding: "10px 12px", borderRadius: 8,
        border: `1.5px solid ${C.border}`, fontSize: 14,
        outline: "none", transition: "border 0.2s", ...props.style,
      }}
      onFocus={e => (e.target.style.border = `1.5px solid ${C.accent}`)}
      onBlur={e  => (e.target.style.border = `1.5px solid ${C.border}`)}
    />
  </div>
);

/* ─── Button ─────────────────────────────────────────────────────────────── */
const Btn = ({ children, variant = "primary", loading, color, ...props }) => {
  const bg = variant === "outline" ? C.white : color || C.primary;
  const fg = variant === "outline" ? (color || C.primary) : C.white;
  return (
    <button
      {...props}
      disabled={loading || props.disabled}
      style={{
        padding: "10px 22px", borderRadius: 8,
        border: variant === "outline" ? `2px solid ${color || C.primary}` : "none",
        background: bg, color: fg, fontWeight: 700, fontSize: 14,
        cursor: loading ? "not-allowed" : "pointer",
        opacity: loading ? 0.7 : 1, transition: "opacity 0.2s", ...props.style,
      }}
      onMouseEnter={e => { if (!loading) e.target.style.opacity = "0.85"; }}
      onMouseLeave={e => { e.target.style.opacity = "1"; }}
    >
      {loading ? "⏳ Please wait…" : children}
    </button>
  );
};

const Badge = ({ children }) => (
  <span style={{
    background: C.light, color: C.primary,
    borderRadius: 20, padding: "3px 12px", fontSize: 12, fontWeight: 700,
  }}>{children}</span>
);

/* ─── TABS ───────────────────────────────────────────────────────────────── */
const TABS = [
  { label: "📋 Candidates" },
  { label: "📄 Offer Letters" },
  { label: "📝 Appointment Letters" },
  { label: "🤝 Joining Letters" },
  { label: "📜 Employment Contract" },
];

/* ═══════════════════════════════════════════════════════════════════════════
   APP ROOT
   ═══════════════════════════════════════════════════════════════════════════ */
export default function App() {
  const [activeTab, setActiveTab] = useState(0);

  return (
    <div style={{ minHeight: "100vh", background: C.bg, fontFamily: "'Segoe UI', sans-serif" }}>

      {/* HEADER */}
      <header style={{
        background: `linear-gradient(135deg, ${C.primary} 0%, ${C.accent} 100%)`,
        color: C.white, padding: "18px 36px",
        display: "flex", alignItems: "center", gap: 16,
        boxShadow: "0 3px 12px rgba(26,35,126,0.3)",
      }}>
        <span style={{ fontSize: 28 }}>🏢</span>
        <div>
          <h1 style={{ margin: 0, fontSize: 22, fontWeight: 800 }}>Bit Byte Technologies</h1>
          <p style={{ margin: 0, fontSize: 12, opacity: 0.8 }}>
            Candidate Management &amp; Letter Generator
          </p>
        </div>
      </header>

      {/* TABS */}
      <div style={{
        display: "flex", gap: 4, padding: "12px 36px 0",
        borderBottom: `2px solid ${C.border}`, background: C.white,
        overflowX: "auto",
      }}>
        {TABS.map((t, i) => (
          <button key={i} onClick={() => setActiveTab(i)} style={{
            padding: "10px 20px", border: "none", whiteSpace: "nowrap",
            borderBottom: activeTab === i ? `3px solid ${C.primary}` : "3px solid transparent",
            background: "transparent",
            color: activeTab === i ? C.primary : C.muted,
            fontWeight: activeTab === i ? 800 : 500,
            fontSize: 14, cursor: "pointer", transition: "color 0.2s",
          }}>{t.label}</button>
        ))}
      </div>

      {/* CONTENT */}
      <main style={{ padding: "28px 36px", maxWidth: 900, margin: "0 auto" }}>
        {activeTab === 0 && <CandidatesTab />}
        {activeTab === 1 && <LetterTab
          title="📄 Generate Offer Letters from Excel"
          description="Upload Excel with candidate data. One candidate → PDF. Multiple → ZIP."
          apiEndpoint={`${API}/generate-offer-letters/`}
          btnLabel="🚀 Generate Offer Letter(s)"
          successSingle="✅ Offer Letter generated!"
          successMulti="✅ Multiple Offer Letters ready! Download ZIP."
          accentColor={C.primary}
          letterType="offer"
        />}
        {activeTab === 2 && <LetterTab
          title="📝 Generate Appointment Letters from Excel"
          description="Upload Excel with joined candidate data. One → PDF. Multiple → ZIP."
          apiEndpoint={`${API}/generate-appointment-letters/`}
          btnLabel="🚀 Generate Appointment Letter(s)"
          successSingle="✅ Appointment Letter generated!"
          successMulti="✅ Multiple Appointment Letters ready! Download ZIP."
          accentColor={C.appt}
          letterType="appointment"
        />}
        {activeTab === 3 && <LetterTab
          title="🤝 Generate Joining Letters from Excel"
          description="Upload Excel with joining candidate data. One → PDF. Multiple → ZIP."
          apiEndpoint={`${API}/generate-joining-letters/`}
          btnLabel="🚀 Generate Joining Letter(s)"
          successSingle="✅ Joining Letter generated!"
          successMulti="✅ Multiple Joining Letters ready! Download ZIP."
          accentColor={C.joining}
          letterType="joining"
        />}
        {activeTab === 4 && <LetterTab
          title="📜 Generate Employment Contracts from Excel"
          description="Upload Excel with employee data. Includes 2-year bond agreement. One → PDF. Multiple → ZIP."
          apiEndpoint={`${API}/generate-contract-letters/`}
          btnLabel="🚀 Generate Contract(s)"
          successSingle="✅ Employment Contract generated!"
          successMulti="✅ Multiple Contracts ready! Download ZIP."
          accentColor={C.contract}
          letterType="contract"
        />}
      </main>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   TAB 1 – Candidates
   ═══════════════════════════════════════════════════════════════════════════ */
function CandidatesTab() {
  const empty = { name:"", email:"", phone:"", previous_company:"", role:"", current_salary:"", expected_salary:"" };
  const [form, setForm]     = useState(empty);
  const [data, setData]     = useState([]);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg]       = useState(null);

  const fetchData = () => axios.get(`${API}/candidates/`).then(r => setData(r.data)).catch(() => {});
  useEffect(() => { fetchData(); }, []);

  const handleSubmit = async () => {
    if (!form.name || !form.email || !form.role) {
      setMsg({ type:"error", text:"Name, Email and Role are required!" }); return;
    }
    setSaving(true);
    try {
      await axios.post(`${API}/candidates/`, form);
      setMsg({ type:"success", text:"✅ Candidate saved successfully!" });
      setForm(empty); fetchData();
    } catch { setMsg({ type:"error", text:"❌ Error saving candidate." }); }
    finally { setSaving(false); setTimeout(() => setMsg(null), 3000); }
  };

  return (
    <>
      <div style={cardStyle}>
        <h2 style={{ ...cardTitle, color: C.primary }}>Add New Candidate</h2>
        <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:16 }}>
          <Input label="Full Name *"          value={form.name}             onChange={e => setForm({...form, name:e.target.value})}             placeholder="Senthil Kumar" />
          <Input label="Email *"              value={form.email}            onChange={e => setForm({...form, email:e.target.value})}            placeholder="senthil@example.com" />
          <Input label="Phone"                value={form.phone}            onChange={e => setForm({...form, phone:e.target.value})}            placeholder="9876543210" />
          <Input label="Previous Company"     value={form.previous_company} onChange={e => setForm({...form, previous_company:e.target.value})} placeholder="Infosys" />
          <Input label="Role *"               value={form.role}             onChange={e => setForm({...form, role:e.target.value})}             placeholder="Software Engineer" />
          <Input label="Current Salary (Rs)"  value={form.current_salary}   onChange={e => setForm({...form, current_salary:e.target.value})}   placeholder="600000" type="number" />
          <Input label="Expected Salary (Rs)" value={form.expected_salary}  onChange={e => setForm({...form, expected_salary:e.target.value})}  placeholder="800000" type="number" />
        </div>
        {msg && (
          <div style={{ marginTop:12, padding:"10px 16px", borderRadius:8,
            background: msg.type==="success"?"#e8f5e9":"#ffebee",
            color: msg.type==="success"?C.success:C.error, fontWeight:600, fontSize:14,
          }}>{msg.text}</div>
        )}
        <div style={{ marginTop:16 }}>
          <Btn loading={saving} onClick={handleSubmit}>💾 Save Candidate</Btn>
        </div>
      </div>

      <h2 style={{ color:C.primary, marginTop:28, marginBottom:12 }}>
        Candidate List <Badge>{data.length}</Badge>
      </h2>
      {data.length === 0
        ? <p style={{ color:C.muted, textAlign:"center", padding:40 }}>No candidates yet.</p>
        : <div style={{ display:"grid", gap:14 }}>
            {data.map(c => (
              <div key={c.id} style={cardStyle}>
                <div style={{ display:"flex", justifyContent:"space-between" }}>
                  <div>
                    <h3 style={{ margin:"0 0 4px", color:C.primary }}>{c.name}</h3>
                    <p style={{ margin:"0 0 8px", fontSize:13, color:C.muted }}>{c.email} · {c.phone}</p>
                  </div>
                  <Badge>{c.role}</Badge>
                </div>
                <div style={{ display:"flex", gap:20, fontSize:13, color:C.text }}>
                  <span>🏢 {c.previous_company||"—"}</span>
                  <span>💰 Rs.{Number(c.current_salary||0).toLocaleString()}</span>
                  <span>🎯 Rs.{Number(c.expected_salary||0).toLocaleString()}</span>
                </div>
              </div>
            ))}
          </div>
      }
    </>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   SHARED LETTER TAB  — Offer / Appointment / Joining / Contract
   ═══════════════════════════════════════════════════════════════════════════ */

const COLS = {
  offer: [
    { col:"name",             req:true  },
    { col:"role",             req:true  },
    { col:"email",            req:false },
    { col:"phone",            req:false },
    { col:"offered_ctc",      req:false },
    { col:"joining_date",     req:false },
    { col:"location",         req:false },
    { col:"previous_company", req:false },
  ],
  appointment: [
    { col:"name",          req:true  },
    { col:"role",          req:true  },
    { col:"employee_id",   req:false },
    { col:"email",         req:false },
    { col:"phone",         req:false },
    { col:"department",    req:false },
    { col:"joining_date",  req:false },
    { col:"offered_ctc",   req:false },
    { col:"location",      req:false },
  ],
  joining: [
    { col:"name",          req:true  },
    { col:"role",          req:true  },
    { col:"employee_id",   req:false },
    { col:"email",         req:false },
    { col:"phone",         req:false },
    { col:"department",    req:false },
    { col:"joining_date",  req:true  },
    { col:"offered_ctc",   req:false },
    { col:"location",      req:false },
    { col:"reporting_to",  req:false },
  ],
  contract: [
    { col:"name",          req:true  },
    { col:"role",          req:true  },
    { col:"employee_id",   req:false },
    { col:"email",         req:false },
    { col:"phone",         req:false },
    { col:"department",    req:false },
    { col:"joining_date",  req:true  },
    { col:"offered_ctc",   req:false },
    { col:"location",      req:false },
    { col:"bond_years",    req:false },
    { col:"reporting_to",  req:false },
  ],
};

function LetterTab({ title, description, apiEndpoint, btnLabel, successSingle, successMulti, accentColor, letterType }) {
  const fileRef               = useRef(null);
  const [file, setFile]       = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult]   = useState(null);
  const [dragOver, setDragOver] = useState(false);

  const cols = COLS[letterType] || COLS.offer;

  const handleFile = f => {
    if (!["xlsx","xls"].some(ext => f.name.toLowerCase().endsWith(ext))) {
      setResult({ type:"error", text:"❌ Only .xlsx or .xls files are supported." }); return;
    }
    setFile(f); setResult(null);
  };

  const handleDrop = e => {
    e.preventDefault(); setDragOver(false);
    if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
  };

  const handleGenerate = async () => {
    if (!file) { setResult({ type:"error", text:"Please upload an Excel file first." }); return; }
    setLoading(true); setResult(null);
    try {
      const fd = new FormData(); fd.append("file", file);
      const res = await axios.post(apiEndpoint, fd, {
        headers: { "Content-Type":"multipart/form-data" }, responseType:"blob",
      });
      const ct    = res.headers["content-type"] || "";
      const disp  = res.headers["content-disposition"] || "";
      const match = disp.match(/filename="?([^"]+)"?/);
      const fname = match ? match[1] : (ct.includes("zip") ? "letters.zip" : "letter.pdf");
      setResult({
        type:"success",
        text: ct.includes("zip") ? successMulti : successSingle,
        downloadUrl: window.URL.createObjectURL(new Blob([res.data])),
        filename: fname,
      });
    } catch (err) {
      let msg = "❌ Error generating letters.";
      if (err.response?.data) {
        try { msg = `❌ ${JSON.parse(await err.response.data.text()).error || msg}`; } catch {}
      }
      setResult({ type:"error", text:msg });
    } finally { setLoading(false); }
  };

  const triggerDownload = () => {
    const a = document.createElement("a");
    a.href = result.downloadUrl; a.download = result.filename; a.click();
  };

  const clearAll = () => { setFile(null); setResult(null); if (fileRef.current) fileRef.current.value=""; };

  return (
    <>
      <div style={cardStyle}>
        <h2 style={{ ...cardTitle, color: accentColor }}>{title}</h2>
        <p style={{ color:C.muted, fontSize:14, marginBottom:20 }}>{description}</p>

        {/* Column guide */}
        <div style={{ background:C.light, borderRadius:10, padding:"14px 18px", marginBottom:20 }}>
          <strong style={{ color:accentColor }}>📊 Excel Columns:</strong>
          <div style={{ marginTop:8, display:"flex", flexWrap:"wrap", gap:8 }}>
            {cols.map(({ col, req }) => (
              <span key={col} style={{
                padding:"4px 10px", borderRadius:6,
                background: req ? accentColor : C.border,
                color: req ? C.white : C.text,
                fontFamily:"monospace", fontSize:12,
              }}>{col}{req?" *":""}</span>
            ))}
          </div>
          <p style={{ margin:"8px 0 0", color:C.muted, fontSize:12 }}>
            * Required columns. Lowercase, underscores use பண்ணு.
          </p>
        </div>

        {/* Drop zone */}
        <div
          onClick={() => fileRef.current.click()}
          onDragOver={e => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          style={{
            border:`2.5px dashed ${dragOver ? accentColor : C.border}`,
            borderRadius:12, padding:"36px 20px", textAlign:"center",
            cursor:"pointer", background: dragOver ? C.light : C.white,
            transition:"all 0.2s", marginBottom:20,
          }}
        >
          <div style={{ fontSize:40, marginBottom:10 }}>📂</div>
          {file ? (
            <>
              <p style={{ color:C.success, fontWeight:700, margin:0 }}>✅ {file.name}</p>
              <p style={{ color:C.muted, fontSize:12, margin:"4px 0 0" }}>{(file.size/1024).toFixed(1)} KB · Click to change</p>
            </>
          ) : (
            <>
              <p style={{ color:accentColor, fontWeight:700, margin:0 }}>Click to upload or drag &amp; drop</p>
              <p style={{ color:C.muted, fontSize:13, margin:"4px 0 0" }}>.xlsx or .xls files only</p>
            </>
          )}
          <input ref={fileRef} type="file" accept=".xlsx,.xls" style={{ display:"none" }}
            onChange={e => e.target.files[0] && handleFile(e.target.files[0])} />
        </div>

        {/* Result */}
        {result && (
          <div style={{
            padding:"14px 18px", borderRadius:10,
            background: result.type==="success"?"#e8f5e9":"#ffebee",
            color: result.type==="success"?C.success:C.error,
            fontWeight:600, fontSize:14, marginBottom:16,
            display:"flex", justifyContent:"space-between", alignItems:"center",
          }}>
            <span>{result.text}</span>
            {result.downloadUrl && (
              <button onClick={triggerDownload} style={{
                padding:"8px 18px", background:accentColor, color:C.white,
                border:"none", borderRadius:8, fontWeight:700, fontSize:13,
                cursor:"pointer", marginLeft:12,
              }}>
                ⬇️ Download {result.filename?.includes("zip") ? "ZIP" : "PDF"}
              </button>
            )}
          </div>
        )}

        <div style={{ display:"flex", gap:12 }}>
          <Btn loading={loading} color={accentColor} onClick={handleGenerate}>{btnLabel}</Btn>
          {file && <Btn variant="outline" color={accentColor} onClick={clearAll}>🗑 Clear</Btn>}
        </div>
      </div>

      {/* Template */}
      <div style={{ ...cardStyle, marginTop:20 }}>
        <h3 style={{ color:accentColor, margin:"0 0 10px" }}>📥 Download Sample Excel Template</h3>
        <p style={{ color:C.muted, fontSize:13, margin:"0 0 14px" }}>
          Fill this template and upload above to generate letters.
        </p>
        <Btn variant="outline" color={accentColor}
          onClick={() => downloadTemplate(letterType)}>
          ⬇️ Download Template
        </Btn>
      </div>
    </>
  );
}

/* ─── Template downloads ─────────────────────────────────────────────────── */
function downloadTemplate(type) {
  const templates = {
    offer: {
      headers: ["name","email","phone","role","previous_company","current_salary","offered_ctc","joining_date","location"],
      sample:  ["Senthil Kumar","senthil@gmail.com","9876543210","Software Engineer","Infosys","600000","800000","2025-06-01","Chennai"],
      file:    "offer_letter_template.csv",
    },
    appointment: {
      headers: ["name","email","phone","role","employee_id","department","joining_date","offered_ctc","location"],
      sample:  ["Senthil Kumar","senthil@gmail.com","9876543210","Software Engineer","EMP001","Engineering","2025-06-01","800000","Chennai"],
      file:    "appointment_letter_template.csv",
    },
    joining: {
      headers: ["name","email","phone","role","employee_id","department","joining_date","offered_ctc","location","reporting_to"],
      sample:  ["Senthil Kumar","senthil@gmail.com","9876543210","Software Engineer","EMP001","Engineering","2025-06-01","800000","Chennai","Mr. Ravi Kumar"],
      file:    "joining_letter_template.csv",
    },
    contract: {
      headers: ["name","email","phone","role","employee_id","department","joining_date","offered_ctc","location","bond_years","reporting_to"],
      sample:  ["Senthil Kumar","senthil@gmail.com","9876543210","Software Engineer","EMP001","Engineering","2025-06-01","800000","Chennai","2","Mr. Ravi Kumar"],
      file:    "contract_template.csv",
    },
  };
  const { headers, sample, file } = templates[type];
  const csv  = [headers.join(","), sample.join(",")].join("\n");
  const blob = new Blob([csv], { type:"text/csv" });
  const a    = document.createElement("a");
  a.href     = URL.createObjectURL(blob);
  a.download = file;
  a.click();
}

/* ─── Shared styles ──────────────────────────────────────────────────────── */
const cardStyle = {
  background:"#ffffff", borderRadius:14, padding:"24px 28px",
  boxShadow:"0 2px 16px rgba(26,35,126,0.08)", border:`1px solid ${C.border}`,
};
const cardTitle = { margin:"0 0 20px", fontSize:18, fontWeight:800 };