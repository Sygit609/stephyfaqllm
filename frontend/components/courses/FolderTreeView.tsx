"use client"

/**
 * Folder Tree View Component
 * Recursive component for displaying nested course structure
 */

import { useState } from "react"
import type { CourseTreeNode } from "@/lib/api/types"
import FolderTreeNode from "./FolderTreeNode"
import AddContentDropdown from "./AddContentDropdown"

interface Props {
  tree: CourseTreeNode
  expandedNodes: Set<string>
  onToggle: (nodeId: string) => void
  onRefresh: () => void
}

export default function FolderTreeView({
  tree,
  expandedNodes,
  onToggle,
  onRefresh
}: Props) {
  return (
    <div className="bg-white rounded-lg shadow-sm overflow-hidden">
      <div className="p-6">
        {/* Course Root Node */}
        <FolderTreeNode
          node={tree}
          level={0}
          isExpanded={expandedNodes.has(tree.id)}
          onToggle={onToggle}
          expandedNodes={expandedNodes}
          onRefresh={onRefresh}
        />
      </div>
    </div>
  )
}
