// This file ONLY exports the raw context object.
// Kept separate so Vite Fast Refresh works correctly.
import { createContext } from 'react';

export const AuthContext = createContext(null);
