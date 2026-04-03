import { v4 as uuidv4 } from 'uuid';

export const generateDeviceSecret = () => {
  return uuidv4(); // Generates a unique 36-character string
};