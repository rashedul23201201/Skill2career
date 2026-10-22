import React from "react";
import { Outlet } from "react-router-dom";
import Navbar from "../components/common/Navbar";
import Footer from "../components/common/Footer";
import ChatWidget from "../components/chat/ChatWidget";

export const MainLayout = () => {
  return (
    <div className="flex flex-col min-h-screen bg-brandBg font-sans text-navy-900">
      <Navbar />
      <main className="flex-grow">
        <Outlet />
      </main>
      <Footer />
      {/* Global Real-time Chat Drawer (SKL-16) */}
      <ChatWidget />
    </div>
  );
};

export default MainLayout;
