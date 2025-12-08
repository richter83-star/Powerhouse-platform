"use strict";

const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("ph", {
  getPaths: () => ipcRenderer.invoke("ph:get-paths"),
  openEnvFile: () => ipcRenderer.invoke("ph:open-env-file"),
  openEnvFolder: () => ipcRenderer.invoke("ph:open-env-folder"),
  relaunch: () => ipcRenderer.invoke("ph:relaunch")
});
