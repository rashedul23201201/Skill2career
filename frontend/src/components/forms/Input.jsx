import React from "react";

export const Input = ({
  label,
  id,
  name,
  type = "text",
  value,
  onChange,
  placeholder = "",
  error = "",
  required = false,
  disabled = false,
  icon: Icon,
  className = "",
  ...rest
}) => {
  return (
    <div className={`w-full ${className}`}>
      {label && (
        <label
          htmlFor={id || name}
          className="block text-sm font-medium text-navy-800 mb-1.5"
        >
          {label} {required && <span className="text-crimson">*</span>}
        </label>
      )}
      <div className="relative rounded-lg shadow-sm">
        {Icon && (
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
            <Icon className="h-5 w-5" />
          </div>
        )}
        <input
          id={id || name}
          name={name}
          type={type}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          required={required}
          disabled={disabled}
          className={`block w-full rounded-lg border text-navy-900 placeholder-slate-400 transition-colors duration-150 sm:text-sm py-2.5 ${
            Icon ? "pl-11" : "pl-3.5"
          } pr-3.5 ${
            error
              ? "border-crimson focus:border-crimson focus:ring-1 focus:ring-crimson"
              : "border-slate-300 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200"
          } ${disabled ? "bg-slate-100 cursor-not-allowed text-slate-500" : "bg-white"}`}
          {...rest}
        />
      </div>
      {error && <p className="mt-1.5 text-xs text-crimson font-medium">{error}</p>}
    </div>
  );
};

export default Input;
