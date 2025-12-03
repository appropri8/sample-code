import { z } from 'zod';

/** Task category enum */
export const CategorySchema = z.enum(['bug', 'feature', 'question', 'other']);
export type Category = z.infer<typeof CategorySchema>;

/** Task triage schema for categorizing and prioritizing issues */
export const TaskTriageSchema = z.object({
  category: CategorySchema,
  priority: z.number().int().min(1).max(5),
  needs_human: z.boolean(),
  summary: z.string().optional(),
}).strict(); // Reject extra fields

export type TaskTriage = z.infer<typeof TaskTriageSchema>;

/** User information extraction schema */
export const UserInfoSchema = z.object({
  name: z.string(),
  email: z.string().email(),
  age: z.number().int().min(0).max(150).optional(),
}).strict();

export type UserInfo = z.infer<typeof UserInfoSchema>;

