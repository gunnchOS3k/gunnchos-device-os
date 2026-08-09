export declare function createDemoBeatmap(id: string, songId: string, bpm: number, durationMs: number, difficulty?: import('@beatlink/shared').DifficultyId): {
    id: string;
    songId: string;
    version: string;
    bpm: number;
    offsetMs: number;
    durationMs: number;
    difficulty: import("@beatlink/shared").DifficultyId;
    licenseStatus: string;
    sections: {
        id: string;
        label: string;
        startMs: number;
        endMs: number;
    }[];
    notes: {
        id: string;
        timeMs: number;
        type: string;
        role: "beat_tapper";
        durationMs: number | undefined;
    }[];
    vocalPrompts: {
        id: string;
        timeMs: number;
        text: string;
        durationMs: number;
    }[];
    hypeEvents: {
        id: string;
        timeMs: number;
        type: "cheer" | "lights" | "boost" | "combo_save";
    }[];
};
//# sourceMappingURL=generator.d.ts.map