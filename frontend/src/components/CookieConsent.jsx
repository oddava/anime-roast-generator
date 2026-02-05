import React from 'react';
import { X, Cookie } from 'lucide-react';

function CookieConsent({ onAccept, onDecline }) {
  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 bg-[#141414] border-t border-[#262626] p-4 shadow-2xl">
      <div className="max-w-6xl mx-auto">
        <div className="flex flex-col md:flex-row items-start md:items-center gap-4">
          <div className="flex items-start gap-3 flex-1">
            <div className="flex-shrink-0 w-10 h-10 bg-[#262626] rounded-full flex items-center justify-center">
              <Cookie className="w-5 h-5 text-[#3b82f6]" />
            </div>
            <div className="flex-1">
              <h4 className="text-white font-medium mb-1">Cookie Consent</h4>
              <p className="text-[#a3a3a3] text-sm leading-relaxed">
                We use cookies to improve your experience and understand how you use our site. 
                This helps us make the roast generator even better!
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-3 w-full md:w-auto">
            <button
              onClick={onDecline}
              className="flex-1 md:flex-none px-4 py-2 bg-transparent hover:bg-[#262626] border border-[#404040] text-[#a3a3a3] hover:text-white rounded-lg text-sm transition-colors"
            >
              Decline
            </button>
            <button
              onClick={onAccept}
              className="flex-1 md:flex-none px-4 py-2 bg-[#3b82f6] hover:bg-[#2563eb] text-white rounded-lg text-sm transition-colors"
            >
              Accept All
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default CookieConsent;
