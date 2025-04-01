using System;
using System.Net;
using System.Text;
using System.Threading;
using UnityEngine;
using UnityEngine.SceneManagement;

public class HttpServer : MonoBehaviour
{
    private HttpListener listener;
    private Thread serverThread;
    private bool isRunning = false;

    // NEW: Cached transform position updated on the main thread.
    private Vector3 cachedTransformPosition;

    // NEW: Static action to be executed on the main thread.
    public static Action ResetAction;

    void Start()
    {
        // Initialize cached transform values on the main thread.
        cachedTransformPosition = transform.position;
        StartServer();
    }

    void StartServer()
    {
        listener = new HttpListener();
        // Listen on port 8001 to avoid conflicts.
        listener.Prefixes.Add("http://127.0.0.1:8001/");
        listener.Start();
        isRunning = true;
        serverThread = new Thread(Listen);
        serverThread.Start();
        Debug.Log("HTTP Server started at http://127.0.0.1:8001/");
    }

    void Listen()
    {
        while (isRunning)
        {
            try
            {
                HttpListenerContext context = listener.GetContext();
                HttpListenerRequest request = context.Request;

                if (request.HttpMethod == "GET")
                {
                    if (request.Url.AbsolutePath.Equals("/ballcount", StringComparison.OrdinalIgnoreCase))
                    {
                        // Use LevelManager.instance.numberOfAgents instead of LevelManager.numberOfAgents.
                        int count = (LevelManager.instance != null) ? LevelManager.instance.numberOfAgents : 0;
                        string jsonResponse = "{\"ball_count\": " + count + "}";
                        HttpListenerResponse response = context.Response;
                        byte[] buffer = Encoding.UTF8.GetBytes(jsonResponse);
                        response.ContentLength64 = buffer.Length;
                        response.ContentType = "application/json";
                        response.OutputStream.Write(buffer, 0, buffer.Length);
                        response.OutputStream.Close();
                        continue;
                    }
                    if (request.Url.AbsolutePath.Equals("/environment", StringComparison.OrdinalIgnoreCase))
                    {
                        // Use the cached transform position instead of accessing transform directly.
                        Vector3 agentPos = cachedTransformPosition;
                        // Get the hole position from GameManager.finishPosition.
                        Vector3 holePos = GameManager.finishPosition;

                        string jsonResponse = "{\"agent_position\": {\"x\": " + agentPos.x +
                                              ", \"y\": " + agentPos.y +
                                              ", \"z\": " + agentPos.z + "}, " +
                                              "\"hole_position\": {\"x\": " + holePos.x +
                                              ", \"y\": " + holePos.y +
                                              ", \"z\": " + holePos.z + "}}";

                        HttpListenerResponse response = context.Response;
                        byte[] buffer = Encoding.UTF8.GetBytes(jsonResponse);
                        response.ContentLength64 = buffer.Length;
                        response.ContentType = "application/json";
                        response.OutputStream.Write(buffer, 0, buffer.Length);
                        response.OutputStream.Close();
                        continue;
                    }
                }
                // Otherwise, handle POST requests as before.
                if (request.HttpMethod == "POST")
                {
                    if (request.Url.AbsolutePath.Equals("/reset", StringComparison.OrdinalIgnoreCase))
                    {
                        Debug.Log("HttpServer: Received /reset POST request. Scheduling level reset.");
                        // Queue the reset action to be executed on the main thread.
                        ResetAction = () => {
                            if (LevelManager.instance != null)
                            {
                                // Reset the level
                                LevelManager.instance.ResetLevel();
                                // After the reset is processed, notify the backend
                                StartCoroutine(NotifyResetComplete());
                            }
                            else
                            {
                                Debug.LogWarning("HttpServer: LevelManager instance not found.");
                            }
                        };
                        
                        HttpListenerResponse response = context.Response;
                        string responseString = "{\"status\": \"reset triggered\"}";
                        byte[] buffer = Encoding.UTF8.GetBytes(responseString);
                        response.ContentLength64 = buffer.Length;
                        response.OutputStream.Write(buffer, 0, buffer.Length);
                        response.OutputStream.Close();
                    }
                    else
                    {
                        using (var reader = new System.IO.StreamReader(request.InputStream, request.ContentEncoding))
                        {
                            string requestBody = reader.ReadToEnd();
                            Debug.Log($"HttpServer: Received POST: {requestBody}");
                        }
                        HttpListenerResponse response = context.Response;
                        string responseString = "{\"status\": \"received\"}";
                        byte[] buffer = Encoding.UTF8.GetBytes(responseString);
                        response.ContentLength64 = buffer.Length;
                        response.OutputStream.Write(buffer, 0, buffer.Length);
                        response.OutputStream.Close();
                    }
                }
            }
            catch (Exception e)
            {
                Debug.LogError($"HttpServer: Server error: {e.Message}");
            }
        }
    }

    void Update()
    {
        // NEW: Update the cached transform position on the main thread.
        cachedTransformPosition = transform.position;
        // Execute any queued reset action on the main thread.
        if (ResetAction != null)
        {
            ResetAction.Invoke();
            ResetAction = null;
        }
    }

    void OnApplicationQuit()
    {
        StopServer();
    }

    void StopServer()
    {
        isRunning = false;
        if (listener != null && listener.IsListening)
            listener.Stop();
        if (serverThread != null && serverThread.IsAlive)
            serverThread.Join();
    }

    // Add this new method to notify the backend that reset is complete
    private System.Collections.IEnumerator NotifyResetComplete()
    {
        Debug.Log("HttpServer: Notifying backend that reset is complete...");
        string url = "http://127.0.0.1:8000/reset_complete";
        using (UnityEngine.Networking.UnityWebRequest request = UnityEngine.Networking.UnityWebRequest.PostWwwForm(url, ""))
        {
            yield return request.SendWebRequest();
            if (request.result == UnityEngine.Networking.UnityWebRequest.Result.Success)
            {
                Debug.Log("Reset completion notification sent successfully.");
            }
            else
            {
                Debug.LogError("Failed to send reset completion notification: " + request.error);
            }
        }
    }
}
