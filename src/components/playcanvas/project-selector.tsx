'use client';

import { usePlayCanvasStore } from '@/store/playcanvas-store';
import { usePlayCanvasApi } from '@/lib/use-playcanvas-api';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { FolderOpen } from 'lucide-react';

export function ProjectSelector() {
  const { projects, selectedProject, selectProject } = usePlayCanvasStore();
  const { loadApps } = usePlayCanvasApi();

  return (
    <div className="flex items-center gap-2">
      <FolderOpen className="w-4 h-4 text-slate-400" />
      <Select
        value={selectedProject?.projectId?.toString() || ''}
        onValueChange={(val) => {
          const project = projects.find((p) => p.projectId.toString() === val);
          if (project) selectProject(project);
        }}
      >
        <SelectTrigger className="w-[200px] sm:w-[280px] bg-slate-800 border-slate-700 text-white text-sm">
          <SelectValue placeholder="Seleccionar proyecto..." />
        </SelectTrigger>
        <SelectContent className="bg-slate-800 border-slate-700 max-h-64">
          {projects.length === 0 ? (
            <div
              className="px-3 py-2 text-sm text-slate-400 cursor-pointer hover:bg-slate-700"
              onClick={() => loadApps()}
            >
              Cargar proyectos...
            </div>
          ) : (
            projects.map((project) => (
              <SelectItem
                key={project.projectId}
                value={project.projectId.toString()}
                className="text-slate-300 focus:bg-slate-700 focus:text-white"
              >
                <div className="flex flex-col">
                  <span className="font-medium">{project.name}</span>
                  <span className="text-xs text-slate-500">{project.owner} · ID: {project.projectId}</span>
                </div>
              </SelectItem>
            ))
          )}
        </SelectContent>
      </Select>
    </div>
  );
}
