import { Routes, Route } from "react-router-dom";
import Landing from "./components/Landing-Page/Landing";
import Signup from "./components/Auth/Signup";
import SignIn from "./components/Auth/Signin";

export default function App() {
  return (
    <>
      <div className="grain-overlay" aria-hidden="true" />
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/login" element={<SignIn />} />
      </Routes>
    </>
  );
}
