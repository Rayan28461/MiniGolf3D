using System;
using System.Net;
using System.Text;
using System.Threading;
using System.Collections;
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

    // Flag to indicate a specific level is fully loaded and ready for training
    // public static bool isLevelReadyForTraining = false;

    void Start()
    {
        // Initialize cached transform values on the main thread.
        cachedTransformPosition = transform.position;
        // Subscribe to scene loading events
        // SceneManager.sceneLoaded += OnSceneLoaded;
        StartServer();
    }

    // This will be called whenever a scene is loaded
    // void OnSceneLoaded(Scene scene, LoadSceneMode mode)
    // {
    //     StartCoroutine(CheckLevelReady());
    // }

    // IEnumerator CheckLevelReady()
    // {
    //     // Wait for a couple of frames to make sure everything is initialized
    //     yield return null;
    //     yield return null;
        
    //     // Check if LevelManager exists and a level is properly loaded
    //     if (LevelManager.instance != null && LevelManager.instance.currentLevel > 0)
    //     {
    //         isLevelReadyForTraining = true;
    //         Debug.Log($"Level {LevelManager.instance.currentLevel} is fully loaded and ready for training!");
    //     }
    //     else
    //     {
    //         isLevelReadyForTraining = false;
    //         Debug.Log("No specific level loaded yet - training should not start");
    //     }
    // }

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

        // Check if game scene and level are loaded
        bool sceneLoaded = SceneManager.GetActiveScene().isLoaded;
        bool levelManagerExists = LevelManager.instance != null;
        
        if (sceneLoaded && levelManagerExists) {
            Debug.Log("Game scene and level are fully loaded and ready");
        } else {
            Debug.LogWarning($"Game scene loaded: {sceneLoaded}, LevelManager: {levelManagerExists}");
            Debug.LogWarning("Server started but scene or level may not be fully loaded yet");
        }
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
                    if (request.Url.AbsolutePath.Equals("/ball_velocity", StringComparison.OrdinalIgnoreCase)) {
                        Debug.Log("HttpServer: Received /ball_velocity GET request.");
                        // Get agent_id from query parameters
                        int agentId = 1; // Default
                        if (request.QueryString["agent_id"] != null)
                        {
                            int.TryParse(request.QueryString["agent_id"], out agentId);
                        }

                        // Queue ball velocity data gathering to be done on main thread
                        bool isBallMoving = false;

                        // Create a simple event to signal when data is ready
                        var dataReadyEvent = new System.Threading.ManualResetEvent(false);
                        
                        // Queue this action to be executed on main thread in Update()
                        ResetAction = () => {
                            var agent = AgentControl.GetAgentById(agentId);
                            if (agent != null) {
                                // Get the ball's velocity magnitude to determine if it's moving
                                float velocityMagnitude = agent.getBallVelocityMagnitude();
                                // Use the same threshold as in your WaitUntil
                                float stopThreshold = 0.1f; // Adjust this value to match your actual threshold
                                isBallMoving = velocityMagnitude >= stopThreshold;
                                Debug.Log($"Ball velocity: {velocityMagnitude}, Is moving: {isBallMoving}");
                            } else {
                                Debug.LogWarning($"No agent found with ID {agentId}");
                            }
                            // Signal that data is ready
                            dataReadyEvent.Set();
                        };
                        
                        // Wait for main thread to process (with timeout)
                        if (dataReadyEvent.WaitOne(2000)) {
                            string jsonResponse = $"{{\"is_moving\": {isBallMoving.ToString().ToLower()}}}";
                            Debug.Log($"Sending ball velocity data for agent {agentId}: {jsonResponse}");
                            
                            HttpListenerResponse response = context.Response;
                            byte[] buffer = Encoding.UTF8.GetBytes(jsonResponse);
                            response.ContentLength64 = buffer.Length;
                            response.ContentType = "application/json";
                            response.OutputStream.Write(buffer, 0, buffer.Length);
                            response.OutputStream.Close();
                        } else {
                            // Timeout occurred
                            string errorJson = "{\"error\": \"Timeout getting ball velocity data\"}";
                            HttpListenerResponse response = context.Response;
                            response.StatusCode = 500;
                            byte[] buffer = Encoding.UTF8.GetBytes(errorJson);
                            response.ContentLength64 = buffer.Length;
                            response.ContentType = "application/json";
                            response.OutputStream.Write(buffer, 0, buffer.Length);
                            response.OutputStream.Close();
                        }
                        continue;
                    }
                    if (request.Url.AbsolutePath.Equals("/environment", StringComparison.OrdinalIgnoreCase))
                    {
                        // Get agent_id from query parameters
                        int agentId = 1; // Default
                        if (request.QueryString["agent_id"] != null)
                        {
                            int.TryParse(request.QueryString["agent_id"], out agentId);
                        }

                        // Queue environment data gathering to be done on main thread
                        MiniGolfAPI.EnvironmentData envData = null;

                        // Create a simple event to signal when data is ready
                        var dataReadyEvent = new System.Threading.ManualResetEvent(false);
                        
                        // Queue this action to be executed on main thread in Update()
                        ResetAction = () => {
                            // StartCoroutine(WaitForLevelToLoad());
                            // if (!isLevelReadyForTraining) {
                            //     Debug.LogWarning("No specific level loaded yet - cannot provide environment data");
                            //     return;
                            // }
                            var agent = AgentControl.GetAgentById(agentId);
                            if (agent != null) {
                                envData = agent.getEnvironmentData();
                            } else {
                                Debug.LogWarning($"No agent found with ID {agentId}");
                            }
                            // Signal that data is ready
                            dataReadyEvent.Set();
                        };
                        
                        // Wait for main thread to process (with timeout)
                        if (dataReadyEvent.WaitOne(2000)) {
                            string jsonResponse = JsonUtility.ToJson(envData);
                            Debug.Log($"Sending environment data for agent {agentId}: {jsonResponse}");
                            
                            HttpListenerResponse response = context.Response;
                            byte[] buffer = Encoding.UTF8.GetBytes(jsonResponse);
                            response.ContentLength64 = buffer.Length;
                            response.ContentType = "application/json";
                            response.OutputStream.Write(buffer, 0, buffer.Length);
                            response.OutputStream.Close();
                        } else {
                            // Timeout occurred
                            string errorJson = "{\"error\": \"Timeout getting environment data\"}";
                            HttpListenerResponse response = context.Response;
                            response.StatusCode = 500;
                            byte[] buffer = Encoding.UTF8.GetBytes(errorJson);
                            response.ContentLength64 = buffer.Length;
                            response.ContentType = "application/json";
                            response.OutputStream.Write(buffer, 0, buffer.Length);
                            response.OutputStream.Close();
                        }
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
                    if (request.Url.AbsolutePath.Equals("/shoot", StringComparison.OrdinalIgnoreCase))
                    {                        
                        // Get agent_id from query parameters
                        int agentId = 1; // Default
                        if (request.QueryString["agent_id"] != null)
                        {
                            int.TryParse(request.QueryString["agent_id"], out agentId);
                        }

                        string requestBody;
                        using (var reader = new System.IO.StreamReader(request.InputStream, request.ContentEncoding))
                        {
                            requestBody = reader.ReadToEnd();
                        }
                        
                        // Deserialize into ShotData object
                        MiniGolfAPI.ShotData shotData = JsonUtility.FromJson<MiniGolfAPI.ShotData>(requestBody);

                        // Create a simple event to signal when data is ready
                        var dataReadyEvent = new System.Threading.ManualResetEvent(false);

                        // Log the shot data
                        Debug.Log($"HttpServer: Received /shoot POST request for agent {shotData.agent_id}");
                        Debug.Log($"Shot Power: {shotData.power}");
                        Debug.Log($"Shot Direction: {shotData.direction}");

                        ResetAction = () => {
                            var agent = AgentControl.GetAgentById(agentId);
                            if (agent != null) {
                                agent.ApplyShot(shotData.power, shotData.direction);
                            } else {
                                Debug.LogWarning($"No agent found with ID {agentId}");
                            }
                            dataReadyEvent.Set(); // Signal that data is ready
                        };
                        
                        

                        // Wait for main thread to process (with timeout)
                        if (dataReadyEvent.WaitOne(2000)) {
                            HttpListenerResponse response = context.Response;
                            string jsonResponse = "{\"status\": \"shot applied\"}";
                            byte[] buffer = Encoding.UTF8.GetBytes(jsonResponse);
                            response.ContentLength64 = buffer.Length;
                            response.ContentType = "application/json";
                            response.OutputStream.Write(buffer, 0, buffer.Length);
                            response.OutputStream.Close();
                        } else {
                            // Timeout occurred
                            string errorJson = "{\"error\": \"Timeout applying shot.\"}";
                            HttpListenerResponse response = context.Response;
                            response.StatusCode = 500;
                            byte[] buffer = Encoding.UTF8.GetBytes(errorJson);
                            response.ContentLength64 = buffer.Length;
                            response.ContentType = "application/json";
                            response.OutputStream.Write(buffer, 0, buffer.Length);
                            response.OutputStream.Close();
                        }
                        continue;
                    }
                    // else
                    // {
                    //     using (var reader = new System.IO.StreamReader(request.InputStream, request.ContentEncoding))
                    //     {
                    //         string requestBody = reader.ReadToEnd();
                    //         Debug.Log($"HttpServer: Received POST: {requestBody}");
                    //     }
                    //     HttpListenerResponse response = context.Response;
                    //     string responseString = "{\"status\": \"received\"}";
                    //     byte[] buffer = Encoding.UTF8.GetBytes(responseString);
                    //     response.ContentLength64 = buffer.Length;
                    //     response.OutputStream.Write(buffer, 0, buffer.Length);
                    //     response.OutputStream.Close();
                    // }
                }
            }
            catch (Exception e)
            {
                Debug.LogError($"HttpServer: Server error: {e.Message}");
            }
        }
    }

    // IEnumerator WaitForLevelToLoad() {
    //     while (!SceneManager.GetActiveScene().isLoaded || LevelManager.instance == null) {
    //         Debug.Log("[WARNING] Level is not loaded yet.");
    //         yield return null; // Wait 1 frame before checking again
    //     }
    //     Debug.Log("Level is fully loaded.");
    // }

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

    // void OnDestroy()
    // {
    //     // Unsubscribe when this object is destroyed
    //     SceneManager.sceneLoaded -= OnSceneLoaded;
    // }

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
