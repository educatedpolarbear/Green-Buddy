import { useState, useEffect, useCallback } from "react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { Spinner } from "@/components/ui/spinner"
import { Textarea } from "@/components/ui/textarea"
import { format } from "date-fns"
import { ThumbsUp, MessageSquare, ChevronDown, ChevronUp } from "lucide-react"
import { motion } from "framer-motion"
import Link from "next/link"
import { useAuth } from "@/contexts/auth-context"
import { Comment } from "@/types/learning"
import { 
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"

interface BackendComment {
  id: number;
  material_id: number;
  user_id: number;
  username?: string;
  user_avatar?: string;
  content: string;
  parent_id?: number | null;
  created_at: string;
  updated_at?: string;
  replies?: BackendComment[];
  likes_count?: number;
  is_liked?: boolean;
}

interface BackendCommentResponse {
  items: BackendComment[];
  total: number;
  pages: number;
  current_page: number;
}

export interface CommentData extends Comment {}

export interface CommentsProps {
  materialId: number | string
  className?: string
}

function transformComment(backendComment: BackendComment | null | undefined, defaultMaterialId: number | string = 0): Comment {
  if (!backendComment) {
    console.error('Received null or undefined comment from API');
    return {
      id: -1,
      material_id: typeof defaultMaterialId === 'string' ? parseInt(defaultMaterialId, 10) : defaultMaterialId || 0,
      user_id: 0,
      username: 'Unknown',
      parent_id: null,
      content: 'Error loading comment',
      likes_count: 0,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      replies: [],
      is_optimistic: false,
      is_liked: false,
      user_avatar: null
    };
  }
  
  return {
    id: backendComment.id,
    material_id: backendComment.material_id,
    user_id: backendComment.user_id,
    username: backendComment.username || 'Anonymous',
    parent_id: backendComment.parent_id || null,
    content: backendComment.content,
    likes_count: backendComment.likes_count || 0,
    created_at: backendComment.created_at,
    updated_at: backendComment.updated_at || backendComment.created_at,
    user_avatar: backendComment.user_avatar || null,
    replies: Array.isArray(backendComment.replies) 
      ? backendComment.replies.map(reply => transformComment(reply, backendComment.material_id)) 
      : [],
    is_liked: backendComment.is_liked || false
  };
}

function transformCommentsResponse(backendResponse: any, defaultMaterialId: number | string = 0): {
  items: Comment[];
  total: number;
  pages: number;
  current_page: number;
} {

  if (backendResponse && Array.isArray(backendResponse.items)) {
    return {
      items: backendResponse.items.map((comment: any) => transformComment(comment, defaultMaterialId)),
      total: backendResponse.total || 0,
      pages: backendResponse.pages || 1,
      current_page: backendResponse.current_page || 1
    };
  }
  
  if (backendResponse && Array.isArray(backendResponse.comments)) {
    return {
      items: backendResponse.comments.map((comment: any) => transformComment(comment, defaultMaterialId)),
      total: backendResponse.total || backendResponse.comments.length,
      pages: backendResponse.pages || 1,
      current_page: backendResponse.current_page || 1
    };
  }
  
  if (backendResponse && Array.isArray(backendResponse)) {
    return {
      items: backendResponse.map((comment: any) => transformComment(comment, defaultMaterialId)),
      total: backendResponse.length,
      pages: 1,
      current_page: 1
    };
  }
  
  if (backendResponse && backendResponse.data) {
    if (Array.isArray(backendResponse.data)) {
      return {
        items: backendResponse.data.map((comment: any) => transformComment(comment, defaultMaterialId)),
        total: backendResponse.data.length,
        pages: 1,
        current_page: 1
      };
    }
    if (Array.isArray(backendResponse.data.items)) {
      return {
        items: backendResponse.data.items.map((comment: any) => transformComment(comment, defaultMaterialId)),
        total: backendResponse.data.total || backendResponse.data.items.length,
        pages: backendResponse.data.pages || 1,
        current_page: backendResponse.data.current_page || 1
      };
    }
    if (Array.isArray(backendResponse.data.comments)) {
      return {
        items: backendResponse.data.comments.map((comment: any) => transformComment(comment, defaultMaterialId)),
        total: backendResponse.data.total || backendResponse.data.comments.length,
        pages: backendResponse.data.pages || 1,
        current_page: backendResponse.data.current_page || 1
      };
    }
  }
  
  console.error('Unexpected comments response format:', backendResponse);
  return {
    items: [],
    total: 0,
    pages: 1,
    current_page: 1
  };
}

interface CommentItemProps {
  comment: CommentData
  level: number
  replyTo: CommentData | null
  replyContent: string
  isAuthenticated: boolean
  onLikeComment: (commentId: number) => void
  onReply: (comment: CommentData) => void
  onCancelReply: () => void
  onSubmitReply: (e: React.FormEvent) => void
  onChangeReply: (value: string) => void
  maxLevel?: number
}

function CommentItem({
  comment,
  level,
  replyTo,
  replyContent,
  isAuthenticated,
  onLikeComment,
  onReply,
  onCancelReply,
  onSubmitReply,
  onChangeReply,
  maxLevel = 5
}: CommentItemProps) {
  const [isExpanded, setIsExpanded] = useState(level < 3)
  const hasReplies = comment.replies && comment.replies.length > 0
  const isDeep = level >= maxLevel
  const isOptimistic = comment.id < 0
  
  const levelClass = level === 0 
    ? "" 
    : `border-l-2 border-[#e8f2e8] pl-4 ml-${Math.min(level * 2, 6)}`
  
  const avatarSize = level === 0 ? "h-8 w-8" : "h-6 w-6"
  const contentSize = level === 0 ? "text-gray-700" : "text-gray-700 text-sm"
  const buttonSize = level === 0 ? "text-sm" : "text-xs"
  
  return (
    <div className={`${levelClass} ${level > 0 ? "mt-4" : ""} ${isOptimistic ? "opacity-70" : ""}`}>
      {isOptimistic && (
        <div className="absolute right-2 top-2 text-xs text-blue-600 animate-pulse">
          Posting...
        </div>
      )}
      <div className="flex items-center mb-2">
        <Avatar className={avatarSize}>
          <AvatarImage src={comment.user_avatar || "/placeholder.svg?height=32&width=32"} alt={comment.username || 'Anonymous'} />
          <AvatarFallback>{comment.username ? comment.username.substring(0, 2).toUpperCase() : 'AN'}</AvatarFallback>
        </Avatar>
        <div className="ml-2">
          <p className="text-sm font-medium">{comment.username || 'Anonymous'}</p>
          <p className="text-xs text-gray-500">
            {comment.created_at && !isNaN(new Date(comment.created_at).getTime()) 
              ? format(new Date(comment.created_at), 'MMM d, yyyy')
              : 'Unknown date'}
          </p>
        </div>
      </div>
      
      <p className={`${contentSize} mb-3`}>{comment.content}</p>
      
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button 
            className={`${comment.is_liked ? "text-[#2c5530] font-medium" : "text-gray-500"} hover:text-[#2c5530] flex items-center gap-1 ${buttonSize}`}
            onClick={() => onLikeComment(comment.id)}
            disabled={!isAuthenticated || isOptimistic}
          >
            <ThumbsUp className={`h-3 w-3 ${comment.is_liked ? "fill-[#2c5530]" : ""}`} />
            {comment.likes_count}
          </button>
          
          {!isOptimistic && (
            <button 
              className={`text-gray-500 hover:text-[#2c5530] flex items-center gap-1 ${buttonSize}`}
              onClick={() => isAuthenticated && onReply(comment)}
              disabled={!isAuthenticated || isDeep}
            >
              <MessageSquare className="h-3 w-3" />
              Reply
            </button>
          )}
          
          {isOptimistic && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <span className="text-gray-400 italic">Posting...</span>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Reply will be available once the comment is saved</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
          
          {hasReplies && (
            <button 
              className={`text-gray-500 hover:text-[#2c5530] flex items-center gap-1 ${buttonSize}`}
              onClick={() => setIsExpanded(!isExpanded)}
            >
              {isExpanded ? (
                <>
                  <ChevronUp className="h-3 w-3" />
                  Hide replies
                </>
              ) : (
                <>
                  <ChevronDown className="h-3 w-3" />
                  Show {comment.replies?.length} {comment.replies?.length === 1 ? 'reply' : 'replies'}
                </>
              )}
            </button>
          )}
        </div>
      </div>
      
      {/* Reply form */}
      {replyTo && replyTo.id === comment.id && (
        <div className="mt-4 ml-2">
          <form onSubmit={onSubmitReply} className="space-y-3">
            <Textarea 
              placeholder={`Reply to ${replyTo.username}...`}
              value={replyContent}
              onChange={(e) => onChangeReply(e.target.value)}
              className="text-sm min-h-[80px] border-none shadow-sm"
              rows={2}
            />
            <div className="flex gap-2">
              <Button 
                type="submit" 
                size="sm" 
                disabled={!replyContent.trim()}
                className="bg-[#2c5530] hover:bg-[#1a3a1a]"
              >
                Reply
              </Button>
              <Button 
                type="button" 
                variant="outline" 
                size="sm"
                onClick={onCancelReply}
              >
                Cancel
              </Button>
            </div>
          </form>
        </div>
      )}
      
      {/* Nested Replies */}
      {hasReplies && isExpanded && (
        <div className="space-y-4">
          {comment.replies?.map((reply) => (
            <CommentItem
              key={reply.id}
              comment={reply}
              level={level + 1}
              replyTo={replyTo}
              replyContent={replyContent}
              isAuthenticated={isAuthenticated}
              onLikeComment={onLikeComment}
              onReply={onReply}
              onCancelReply={onCancelReply}
              onSubmitReply={onSubmitReply}
              onChangeReply={onChangeReply}
              maxLevel={maxLevel}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export function Comments({
  materialId,
  className
}: CommentsProps) {
  const { user, isAuthenticated } = useAuth();
  const [comments, setComments] = useState<Comment[]>([]);
  const [totalComments, setTotalComments] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [currentPage, setCurrentPage] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [newComment, setNewComment] = useState("");
  const [replyTo, setReplyTo] = useState<CommentData | null>(null);
  const [replyContent, setReplyContent] = useState("");
  
  const fetchComments = useCallback(async (page: number = 1): Promise<void> => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await fetch(
        `/api/learning/comments/material/${materialId}?page=${page}&per_page=10`,
        { cache: 'no-store' }
      );
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to fetch comments');
      }
      
      const backendData = await response.json();
      const data = transformCommentsResponse(backendData, materialId);
      
      setComments(data.items);
      setTotalComments(data.total);
      setTotalPages(data.pages);
      setCurrentPage(data.current_page);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      console.error('Error fetching comments:', err);
    } finally {
      setIsLoading(false);
    }
  }, [materialId]);
  
  const addComment = async (content: string, parentId: number | null = null): Promise<Comment | null> => {
    if (!isAuthenticated) {
      setError('You must be logged in to add comments');
      return null;
    }

    try {
      setError(null);
      
      const currentDate = new Date().toISOString();
      
      let username = user?.username || 'Anonymous';
      let userId = user?.id || 0;
      

      if (!user) {
        const userJSON = localStorage.getItem('user');
        
        if (userJSON) {
          try {
            const userData = JSON.parse(userJSON);
            username = userData.username || 'Anonymous';
            userId = userData.id || 0;
          } catch (e) {
            
            console.error('Error parsing user data from localStorage:', e);
          }
        }
      }
      
            
      const optimisticComment: Comment = {
        id: -Date.now(),
        material_id: typeof materialId === 'string' ? parseInt(materialId, 10) : materialId,
        user_id: userId,
        username: username,
        content: content,
        likes_count: 0,
        created_at: currentDate,
        updated_at: currentDate,
        parent_id: parentId,
        replies: [],
        is_optimistic: true,
        is_liked: false,
        user_avatar: null
      };
      
      if (!parentId) {
        setComments(prevComments => [optimisticComment, ...prevComments]);
        setTotalComments(prev => prev + 1);
      } else {
        setComments(prevComments => 
          prevComments.map(comment => {
            if (comment.id === parentId) {
              return {
                ...comment,
                replies: [...comment.replies, optimisticComment]
              };
            }
            return comment;
          })
        );
      }
      
      setIsLoading(true);
      
      const token = localStorage.getItem('token');
      
      const response = await fetch(`/api/learning/comments/material/${materialId}`, {
        method: 'POST',
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ content, parent_id: parentId })
      });
      
      if (!response.ok) {
        if (!parentId) {
          setComments(prevComments => prevComments.filter(c => c.id !== optimisticComment.id));
          setTotalComments(prev => prev - 1);
        } else {
          setComments(prevComments => 
            prevComments.map(comment => {
              if (comment.id === parentId) {
                return {
                  ...comment,
                  replies: comment.replies.filter(r => r.id !== optimisticComment.id)
                };
              }
              return comment;
            })
          );
        }
        
        throw new Error('Failed to add comment');
      }
      
      const responseData = await response.json();
      const rawComment = responseData.data?.comment || responseData;
      const transformedComment = transformComment(rawComment, materialId);

      const newComment: Comment = {
        ...optimisticComment, 
        ...transformedComment, 
        
        id: transformedComment.id || optimisticComment.id,
        material_id: optimisticComment.material_id, 
        user_id: optimisticComment.user_id,
        username: optimisticComment.username,
        content: optimisticComment.content,
        created_at: optimisticComment.created_at,
        updated_at: optimisticComment.updated_at,
        
        is_optimistic: false
      };
      
      if (!parentId) {
        setComments(prevComments => 
          prevComments.map(c => c.id === optimisticComment.id ? newComment : c)
        );
      } else {
        setComments(prevComments => 
          prevComments.map(comment => {
            if (comment.id === parentId) {
              return {
                ...comment,
                replies: comment.replies.map(reply => 
                  reply.id === optimisticComment.id ? newComment : reply
                )
              };
            }
            return comment;
          })
        );
      }
      
      return newComment;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      console.error('Error adding comment:', err);
      return null;
    } finally {
      setIsLoading(false);
    }
  };
  
  const toggleCommentLike = async (commentId: number): Promise<void> => {
    if (!isAuthenticated) {
      setError('You must be logged in to like comments');
      return;
    }

    try {
      setError(null);
      
      const updateCommentLikes = (comments: Comment[], targetId: number, increment: boolean): Comment[] => {
        return comments.map(comment => {
          if (comment.id === targetId) {
            return { 
              ...comment, 
              likes_count: comment.likes_count + (increment ? 1 : -1),
              is_liked: increment 
            };
          }
          
          if (comment.replies && comment.replies.length > 0) {
            return {
              ...comment,
              replies: updateCommentLikes(comment.replies, targetId, increment)
            };
          }
          
          return comment;
        });
      };
      
      let isAlreadyLiked = false;
      
      const findLikedStatus = (comments: Comment[], id: number): boolean => {
        for (const comment of comments) {
          if (comment.id === id) {
            return !!comment.is_liked;
          }
          if (comment.replies) {
            const foundInReplies = findLikedStatus(comment.replies, id);
            if (foundInReplies !== null) {
              return foundInReplies;
            }
          }
        }
        return false;
      };
      
      isAlreadyLiked = findLikedStatus(comments, commentId);
      
      setComments(prevComments => 
        updateCommentLikes(prevComments, commentId, !isAlreadyLiked)
      );
      
      const token = localStorage.getItem('token');
      
      const response = await fetch(`/api/learning/comments/${commentId}/like`, {
        method: 'POST',
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
          'Content-Type': 'application/json',
        }
      });
      
      if (!response.ok) {
        setComments(prevComments => 
          updateCommentLikes(prevComments, commentId, isAlreadyLiked)
        );
        
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to toggle comment like');
      }
      
      const responseData = await response.json();
      if (responseData.data && responseData.data.comment) {
        const transformedComment = transformComment(responseData.data.comment, materialId);
        
        const findComment = (comments: Comment[], id: number): Comment | null => {
          for (const comment of comments) {
            if (comment.id === id) {
              return comment;
            }
            if (comment.replies && comment.replies.length > 0) {
              const foundInReplies = findComment(comment.replies, id);
              if (foundInReplies) {
                return foundInReplies;
              }
            }
          }
          return null;
        };
        
        const originalComment = findComment(comments, commentId);
        
        const updatedComment: Comment = originalComment ? {
          ...originalComment,                    
          ...transformedComment,                 
          id: transformedComment.id || originalComment.id,
          material_id: transformedComment.material_id || originalComment.material_id,
          username: transformedComment.username || originalComment.username,
          content: transformedComment.content || originalComment.content,
          likes_count: transformedComment.likes_count !== undefined ? 
                       transformedComment.likes_count : originalComment.likes_count,
          is_liked: transformedComment.is_liked !== undefined ? 
                     transformedComment.is_liked : !isAlreadyLiked
        } : transformedComment;
        
        const updateCommentWithServerData = (comments: Comment[], updatedComment: Comment): Comment[] => {
          return comments.map(comment => {
            if (comment.id === updatedComment.id) {
              return updatedComment;
            }
            if (comment.replies && comment.replies.length > 0) {
              return {
                ...comment,
                replies: updateCommentWithServerData(comment.replies, updatedComment)
              };
            }
            return comment;
          });
        };
        
        setComments(prevComments => updateCommentWithServerData(prevComments, updatedComment));
      }
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      console.error('Error toggling comment like:', err);
    }
  };
  
  const handleSubmitComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newComment.trim()) return;
    
    const result = await addComment(newComment);
    if (result) {
      setNewComment("");
    }
  };
  
  const handleSubmitReply = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!replyContent.trim() || !replyTo) return;
    
    const parentId = replyTo.id;
    
    const result = await addComment(replyContent, parentId);
    if (result) {
      setReplyContent("");
      setReplyTo(null);
    }
  };
  
  const handleLikeComment = (commentId: number) => {
    toggleCommentLike(commentId);
  };
  
  const handleReply = (comment: CommentData) => {
    setReplyTo(comment);
    setReplyContent("");
  };
  
  const handleCancelReply = () => {
    setReplyTo(null);
    setReplyContent("");
  };
  
  useEffect(() => {
    fetchComments(1);
  }, [fetchComments, materialId]);
  
  return (
    <div id="comments" className={className}>
      <motion.section 
        variants={{
          hidden: { opacity: 0, y: 20 },
          visible: { opacity: 1, y: 0 }
        }}
        className="space-y-6"
      >
        <h2 className="text-2xl font-bold text-[#2c5530]">Comments ({totalComments})</h2>
        
        {isAuthenticated ? (
          <form onSubmit={handleSubmitComment} className="mb-8">
            <Textarea 
              placeholder="Share your thoughts..."
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              className="mb-4 min-h-[100px] border-none shadow-sm"
              rows={3}
            />
            <Button 
              type="submit" 
              disabled={!newComment.trim()}
              className="bg-[#2c5530] hover:bg-[#1a3a1a]"
            >
              Post Comment
            </Button>
          </form>
        ) : (
          <Alert className="mb-8">
            <AlertDescription>
              Please <Link href="/login" className="text-[#2c5530] font-medium">sign in</Link> to leave a comment.
            </AlertDescription>
          </Alert>
        )}
        
        {isLoading && comments.length === 0 ? (
          <div className="flex justify-center py-8">
            <Spinner />
          </div>
        ) : comments.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No comments yet. Be the first to share your thoughts!
          </div>
        ) : (
          <div className="space-y-6">
            {comments.map((comment) => (
              <div key={comment.id} className="bg-white border border-gray-100 shadow-sm rounded-lg p-4 relative">
                <CommentItem
                  comment={comment}
                  level={0}
                  replyTo={replyTo}
                  replyContent={replyContent}
                  isAuthenticated={isAuthenticated}
                  onLikeComment={handleLikeComment}
                  onReply={handleReply} 
                  onCancelReply={handleCancelReply}
                  onSubmitReply={handleSubmitReply}
                  onChangeReply={setReplyContent}
                />
              </div>
            ))}
            
            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex justify-center gap-2 mt-8">
                {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                  <Button
                    key={page}
                    variant={page === currentPage ? "default" : "outline"}
                    size="sm"
                    onClick={() => fetchComments(page)}
                    className={page === currentPage ? "bg-[#2c5530] hover:bg-[#1a3a1a] w-10" : "w-10"}
                  >
                    {page}
                  </Button>
                ))}
              </div>
            )}
          </div>
        )}
      </motion.section>
    </div>
  )
} 
