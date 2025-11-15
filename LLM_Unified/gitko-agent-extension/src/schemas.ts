import { z } from 'zod';

/**
 * Task Queue Schemas - Zod-based validation for task payloads
 */

// Base task schema
export const TaskSchema = z.object({
    task_id: z.string(),
    type: z.string(),
    data: z.unknown(),
    created_at: z.string().optional(),
});

export type Task = z.infer<typeof TaskSchema>;

// Computer Use task data schemas
export const ScanScreenDataSchema = z.object({
    text: z.string().optional(),
    region: z
        .object({
            x: z.number(),
            y: z.number(),
            width: z.number(),
            height: z.number(),
        })
        .optional(),
});

export const FindTextDataSchema = z.object({
    text: z.string(),
    region: z
        .object({
            x: z.number(),
            y: z.number(),
            width: z.number(),
            height: z.number(),
        })
        .optional(),
});

export const ClickDataSchema = z.union([
    z.object({
        text: z.string(),
        region: z
            .object({
                x: z.number(),
                y: z.number(),
                width: z.number(),
                height: z.number(),
            })
            .optional(),
    }),
    z.object({
        x: z.number(),
        y: z.number(),
    }),
]);

export const TypeDataSchema = z.object({
    text: z.string(),
    pressEnter: z.boolean().optional(),
});

// Task type mapping
export const ComputerUseTaskSchema = z.discriminatedUnion('type', [
    z.object({
        task_id: z.string(),
        type: z.literal('computer_use.scan'),
        data: ScanScreenDataSchema,
        created_at: z.string().optional(),
    }),
    z.object({
        task_id: z.string(),
        type: z.literal('computer_use.find'),
        data: FindTextDataSchema,
        created_at: z.string().optional(),
    }),
    z.object({
        task_id: z.string(),
        type: z.literal('computer_use.click'),
        data: ClickDataSchema,
        created_at: z.string().optional(),
    }),
    z.object({
        task_id: z.string(),
        type: z.literal('computer_use.type'),
        data: TypeDataSchema,
        created_at: z.string().optional(),
    }),
]);

// Generic task types
export const GenericTaskSchema = z.union([
    z.object({
        task_id: z.string(),
        type: z.literal('ping'),
        data: z.unknown(),
        created_at: z.string().optional(),
    }),
    z.object({
        task_id: z.string(),
        type: z.literal('calculation'),
        data: z.object({
            operation: z.string(),
            a: z.number(),
            b: z.number(),
        }),
        created_at: z.string().optional(),
    }),
    z.object({
        task_id: z.string(),
        type: z.literal('data_transform'),
        data: z.object({
            transform: z.string(),
            input: z.unknown(),
        }),
        created_at: z.string().optional(),
    }),
    z.object({
        task_id: z.string(),
        type: z.literal('batch_calculation'),
        data: z.object({
            operations: z.array(
                z.object({
                    operation: z.string(),
                    a: z.number(),
                    b: z.number(),
                })
            ),
        }),
        created_at: z.string().optional(),
    }),
]);

// All tasks union
export const AllTasksSchema = z.union([ComputerUseTaskSchema, GenericTaskSchema]);

// Submit result schema
export const SubmitResultSchema = z.object({
    success: z.boolean(),
    data: z.unknown().optional(),
    error: z.string().optional(),
});

export type SubmitResult = z.infer<typeof SubmitResultSchema>;

// Task response (from server)
export const TaskResponseSchema = z.union([TaskSchema, z.object({ task: z.null() }), z.null()]);

/**
 * Validate and parse a task
 */
export function validateTask(rawTask: unknown): Task {
    return TaskSchema.parse(rawTask);
}

/**
 * Validate task with detailed error reporting
 */
export function validateTaskSafe(rawTask: unknown): { success: true; data: Task } | { success: false; error: string } {
    const result = TaskSchema.safeParse(rawTask);
    if (result.success) {
        return { success: true, data: result.data };
    }
    return {
        success: false,
        error: result.error.issues.map((e) => `${e.path.join('.')}: ${e.message}`).join(', '),
    };
}

/**
 * Validate Computer Use task
 */
export function validateComputerUseTask(
    rawTask: unknown
): { success: true; data: z.infer<typeof ComputerUseTaskSchema> } | { success: false; error: string } {
    const result = ComputerUseTaskSchema.safeParse(rawTask);
    if (result.success) {
        return { success: true, data: result.data };
    }
    return {
        success: false,
        error: result.error.issues.map((e) => `${e.path.join('.')}: ${e.message}`).join(', '),
    };
}

/**
 * Type guard for Computer Use tasks
 */
export function isComputerUseTask(task: Task): task is z.infer<typeof ComputerUseTaskSchema> {
    return task.type.startsWith('computer_use.');
}
