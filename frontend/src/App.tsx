import { Routes, Route } from "react-router-dom";
import Landing from "./components/Landing-Page/Landing";
import Signup from "./components/Auth/Signup";

export default function App() {
  return (
    <>
      <div className="grain-overlay" aria-hidden="true" />
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/signup" element={<Signup />} />
      </Routes>
    </>
  );
}
